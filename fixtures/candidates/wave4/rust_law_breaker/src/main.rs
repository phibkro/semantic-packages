mod stack;

use stack::Stack;
use std::collections::HashMap;
use std::io::{self, BufRead, Write};
use std::process::ExitCode;

#[derive(Debug)]
enum Json {
    Object(Vec<(String, Json)>),
    String(String),
    Integer(i64),
}

struct Parser {
    input: Vec<char>,
    cursor: usize,
}

impl Parser {
    fn new(input: &str) -> Self {
        Self {
            input: input.chars().collect(),
            cursor: 0,
        }
    }

    fn parse(mut self) -> Result<Json, String> {
        self.skip_whitespace();
        let value = self.parse_value()?;
        self.skip_whitespace();
        if self.cursor != self.input.len() {
            return Err("trailing input after JSON value".to_owned());
        }
        Ok(value)
    }

    fn parse_value(&mut self) -> Result<Json, String> {
        self.skip_whitespace();
        match self.peek() {
            Some('{') => self.parse_object(),
            Some('"') => self.parse_string().map(Json::String),
            Some('-' | '0'..='9') => self.parse_integer().map(Json::Integer),
            _ => Err("expected a request JSON object, string, or integer".to_owned()),
        }
    }

    fn parse_object(&mut self) -> Result<Json, String> {
        self.expect('{')?;
        self.skip_whitespace();
        let mut members = Vec::new();
        if self.take_if('}') {
            return Ok(Json::Object(members));
        }

        loop {
            self.skip_whitespace();
            let key = self.parse_string()?;
            self.skip_whitespace();
            self.expect(':')?;
            let value = self.parse_value()?;
            members.push((key, value));
            self.skip_whitespace();
            if self.take_if('}') {
                return Ok(Json::Object(members));
            }
            self.expect(',')?;
        }
    }

    fn parse_string(&mut self) -> Result<String, String> {
        self.expect('"')?;
        let mut output = String::new();
        loop {
            let character = self
                .next()
                .ok_or_else(|| "unterminated JSON string".to_owned())?;
            match character {
                '"' => return Ok(output),
                '\\' => {
                    let escaped = self
                        .next()
                        .ok_or_else(|| "unterminated JSON escape".to_owned())?;
                    match escaped {
                        '"' | '\\' | '/' => output.push(escaped),
                        'b' => output.push('\u{0008}'),
                        'f' => output.push('\u{000c}'),
                        'n' => output.push('\n'),
                        'r' => output.push('\r'),
                        't' => output.push('\t'),
                        'u' => output.push(self.parse_unicode_escape()?),
                        _ => return Err("unsupported JSON string escape".to_owned()),
                    }
                }
                '\u{0000}'..='\u{001f}' => {
                    return Err("unescaped control character in JSON string".to_owned());
                }
                other => output.push(other),
            }
        }
    }

    fn parse_unicode_escape(&mut self) -> Result<char, String> {
        let first = self.parse_hex_quad()?;
        let scalar = if (0xd800..=0xdbff).contains(&first) {
            self.expect('\\')?;
            self.expect('u')?;
            let second = self.parse_hex_quad()?;
            if !(0xdc00..=0xdfff).contains(&second) {
                return Err("invalid low surrogate in JSON string".to_owned());
            }
            0x10000 + (((first - 0xd800) as u32) << 10) + (second - 0xdc00) as u32
        } else if (0xdc00..=0xdfff).contains(&first) {
            return Err("unpaired low surrogate in JSON string".to_owned());
        } else {
            first as u32
        };
        char::from_u32(scalar).ok_or_else(|| "invalid Unicode scalar value".to_owned())
    }

    fn parse_hex_quad(&mut self) -> Result<u16, String> {
        let mut value = 0_u16;
        for _ in 0..4 {
            let digit = self
                .next()
                .and_then(|character| character.to_digit(16))
                .ok_or_else(|| "invalid JSON Unicode escape".to_owned())?;
            value = value * 16 + digit as u16;
        }
        Ok(value)
    }

    fn parse_integer(&mut self) -> Result<i64, String> {
        let start = self.cursor;
        self.take_if('-');
        match self.peek() {
            Some('0') => {
                self.cursor += 1;
                if matches!(self.peek(), Some('0'..='9')) {
                    return Err("leading zero in JSON integer".to_owned());
                }
            }
            Some('1'..='9') => {
                self.cursor += 1;
                while matches!(self.peek(), Some('0'..='9')) {
                    self.cursor += 1;
                }
            }
            _ => return Err("invalid JSON integer".to_owned()),
        }
        let text: String = self.input[start..self.cursor].iter().collect();
        text.parse::<i64>()
            .map_err(|_| "JSON integer is outside the supported i64 range".to_owned())
    }

    fn skip_whitespace(&mut self) {
        while matches!(self.peek(), Some(' ' | '\t' | '\n' | '\r')) {
            self.cursor += 1;
        }
    }

    fn expect(&mut self, expected: char) -> Result<(), String> {
        match self.next() {
            Some(actual) if actual == expected => Ok(()),
            _ => Err(format!("expected JSON character {expected:?}")),
        }
    }

    fn take_if(&mut self, expected: char) -> bool {
        if self.peek() == Some(expected) {
            self.cursor += 1;
            true
        } else {
            false
        }
    }

    fn peek(&self) -> Option<char> {
        self.input.get(self.cursor).copied()
    }

    fn next(&mut self) -> Option<char> {
        let value = self.peek()?;
        self.cursor += 1;
        Some(value)
    }
}

enum Request {
    Empty { seq: i64 },
    Push { seq: i64, stack: String, value: i64 },
    Pop { seq: i64, stack: String },
}

fn exact_object<'a>(value: &'a Json, expected: &[&str]) -> Result<&'a [(String, Json)], String> {
    let Json::Object(members) = value else {
        return Err("expected JSON object".to_owned());
    };
    if members.len() != expected.len() {
        return Err("JSON object has unexpected member count".to_owned());
    }
    for name in expected {
        if members.iter().filter(|(key, _)| key == name).count() != 1 {
            return Err(format!("JSON object must contain exactly one {name:?} member"));
        }
    }
    Ok(members)
}

fn member<'a>(members: &'a [(String, Json)], name: &str) -> &'a Json {
    &members
        .iter()
        .find(|(key, _)| key == name)
        .expect("exact_object established the requested member")
        .1
}

fn integer(value: &Json, name: &str) -> Result<i64, String> {
    match value {
        Json::Integer(value) => Ok(*value),
        _ => Err(format!("{name} must be a JSON integer")),
    }
}

fn string(value: &Json, name: &str) -> Result<String, String> {
    match value {
        Json::String(value) => Ok(value.clone()),
        _ => Err(format!("{name} must be a JSON string")),
    }
}

fn parse_request(line: &str) -> Result<Request, String> {
    let document = Parser::new(line).parse()?;
    let root = exact_object(&document, &["seq", "op", "args"])?;
    let seq = integer(member(root, "seq"), "seq")?;
    if seq < 0 {
        return Err("seq must be nonnegative".to_owned());
    }
    let op = string(member(root, "op"), "op")?;
    let args = member(root, "args");
    match op.as_str() {
        "empty" => {
            exact_object(args, &[])?;
            Ok(Request::Empty { seq })
        }
        "push" => {
            let args = exact_object(args, &["stack", "value"])?;
            Ok(Request::Push {
                seq,
                stack: string(member(args, "stack"), "stack")?,
                value: integer(member(args, "value"), "value")?,
            })
        }
        "pop" => {
            let args = exact_object(args, &["stack"])?;
            Ok(Request::Pop {
                seq,
                stack: string(member(args, "stack"), "stack")?,
            })
        }
        _ => Err("unknown operation in valid-request fixture".to_owned()),
    }
}

struct Session {
    stacks: HashMap<String, Stack>,
    next_handle: usize,
    changed_first_nonempty_pop: bool,
}

impl Session {
    fn new() -> Self {
        Self {
            stacks: HashMap::new(),
            next_handle: 0,
            changed_first_nonempty_pop: false,
        }
    }

    fn store(&mut self, stack: Stack) -> String {
        let handle = format!("h{}", self.next_handle);
        self.next_handle += 1;
        self.stacks.insert(handle.clone(), stack);
        handle
    }

    fn stack(&self, handle: &str) -> Result<Stack, String> {
        self.stacks
            .get(handle)
            .cloned()
            .ok_or_else(|| format!("unknown session handle {handle:?}"))
    }

    fn respond(&mut self, request: Request) -> Result<String, (i64, String)> {
        match request {
            Request::Empty { seq } => {
                let handle = self.store(Stack::empty());
                Ok(format!(
                    "{{\"seq\":{seq},\"status\":\"ok\",\"result\":{{\"stack\":\"{handle}\"}},\"events\":[]}}"
                ))
            }
            Request::Push {
                seq,
                stack,
                value,
            } => {
                let source = self.stack(&stack).map_err(|message| (seq, message))?;
                let handle = self.store(source.push(value));
                Ok(format!(
                    "{{\"seq\":{seq},\"status\":\"ok\",\"result\":{{\"stack\":\"{handle}\"}},\"events\":[]}}"
                ))
            }
            Request::Pop { seq, stack } => {
                let source = self.stack(&stack).map_err(|message| (seq, message))?;
                match source.pop() {
                    None => Ok(format!(
                        "{{\"seq\":{seq},\"status\":\"ok\",\"result\":{{\"tag\":\"none\"}},\"events\":[]}}"
                    )),
                    Some((value, remainder)) => {
                        let handle = self.store(remainder);
                        // Intentional fixture behavior: challenge exactly the first
                        // nonempty pop value while keeping the correct remainder.
                        let reported_value = if self.changed_first_nonempty_pop {
                            value
                        } else {
                            self.changed_first_nonempty_pop = true;
                            value + 1
                        };
                        Ok(format!(
                            "{{\"seq\":{seq},\"status\":\"ok\",\"result\":{{\"tag\":\"some\",\"value\":{reported_value},\"remainder\":\"{handle}\"}},\"events\":[]}}"
                        ))
                    }
                }
            }
        }
    }
}

fn error_response(seq: i64, message: &str) -> String {
    let escaped = message.replace('\\', "\\\\").replace('"', "\\\"");
    format!(
        "{{\"seq\":{seq},\"status\":\"error\",\"error\":{{\"code\":\"adapter-error\",\"message\":\"{escaped}\"}},\"events\":[]}}"
    )
}

fn run() -> Result<(), String> {
    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut output = stdout.lock();
    let mut session = Session::new();

    for line in stdin.lock().lines() {
        let line = line.map_err(|error| format!("failed to read stdin: {error}"))?;
        let request = parse_request(&line)?;
        let response = match session.respond(request) {
            Ok(response) => response,
            Err((seq, message)) => error_response(seq, &message),
        };
        writeln!(output, "{response}")
            .and_then(|_| output.flush())
            .map_err(|error| format!("failed to write stdout: {error}"))?;
    }
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(message) => {
            eprintln!("rust-law-breaker: {message}");
            ExitCode::from(2)
        }
    }
}

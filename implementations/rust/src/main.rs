mod stack;

use stack::Stack;
use std::collections::HashMap;
use std::io::{self, BufRead, Write};

#[derive(Debug)]
enum Json {
    Object(Vec<(String, Json)>),
    String(String),
    Integer(String),
}

struct Parser<'a> {
    input: &'a [u8],
    position: usize,
}

impl<'a> Parser<'a> {
    fn new(input: &'a str) -> Self {
        Self {
            input: input.as_bytes(),
            position: 0,
        }
    }

    fn parse(mut self) -> Result<Json, String> {
        let value = self.value()?;
        self.whitespace();
        if self.position != self.input.len() {
            return Err("trailing input after JSON value".to_owned());
        }
        Ok(value)
    }

    fn value(&mut self) -> Result<Json, String> {
        self.whitespace();
        match self.peek() {
            Some(b'{') => self.object(),
            Some(b'\"') => self.string().map(Json::String),
            Some(b'-' | b'0'..=b'9') => self.integer().map(Json::Integer),
            _ => Err("expected a JSON value".to_owned()),
        }
    }

    fn object(&mut self) -> Result<Json, String> {
        self.expect(b'{')?;
        self.whitespace();
        let mut members = Vec::new();
        if self.consume(b'}') {
            return Ok(Json::Object(members));
        }
        loop {
            self.whitespace();
            let key = self.string()?;
            self.whitespace();
            self.expect(b':')?;
            let value = self.value()?;
            members.push((key, value));
            self.whitespace();
            if self.consume(b'}') {
                return Ok(Json::Object(members));
            }
            self.expect(b',')?;
        }
    }

    fn string(&mut self) -> Result<String, String> {
        self.expect(b'\"')?;
        let mut output = Vec::new();
        loop {
            let byte = self
                .next()
                .ok_or_else(|| "unterminated JSON string".to_owned())?;
            match byte {
                b'\"' => {
                    return String::from_utf8(output)
                        .map_err(|_| "JSON string is not valid UTF-8".to_owned());
                }
                b'\\' => match self
                    .next()
                    .ok_or_else(|| "unterminated JSON escape".to_owned())?
                {
                    b'\"' => output.push(b'\"'),
                    b'\\' => output.push(b'\\'),
                    b'/' => output.push(b'/'),
                    b'b' => output.push(0x08),
                    b'f' => output.push(0x0c),
                    b'n' => output.push(b'\n'),
                    b'r' => output.push(b'\r'),
                    b't' => output.push(b'\t'),
                    b'u' => {
                        let scalar = self.hex_scalar()?;
                        let character = char::from_u32(scalar)
                            .ok_or_else(|| "unsupported JSON Unicode scalar".to_owned())?;
                        let mut encoded = [0_u8; 4];
                        output.extend_from_slice(character.encode_utf8(&mut encoded).as_bytes());
                    }
                    _ => return Err("invalid JSON escape".to_owned()),
                },
                0x00..=0x1f => return Err("control byte in JSON string".to_owned()),
                other => output.push(other),
            }
        }
    }

    fn hex_scalar(&mut self) -> Result<u32, String> {
        let mut value = 0_u32;
        for _ in 0..4 {
            let digit = match self
                .next()
                .ok_or_else(|| "short JSON Unicode escape".to_owned())?
            {
                b'0'..=b'9' => u32::from(self.input[self.position - 1] - b'0'),
                b'a'..=b'f' => u32::from(self.input[self.position - 1] - b'a') + 10,
                b'A'..=b'F' => u32::from(self.input[self.position - 1] - b'A') + 10,
                _ => return Err("invalid JSON Unicode escape".to_owned()),
            };
            value = value * 16 + digit;
        }
        Ok(value)
    }

    fn integer(&mut self) -> Result<String, String> {
        let start = self.position;
        self.consume(b'-');
        match self.peek() {
            Some(b'0') => {
                self.position += 1;
                if matches!(self.peek(), Some(b'0'..=b'9')) {
                    return Err("leading zero in JSON integer".to_owned());
                }
            }
            Some(b'1'..=b'9') => {
                self.position += 1;
                while matches!(self.peek(), Some(b'0'..=b'9')) {
                    self.position += 1;
                }
            }
            _ => return Err("invalid JSON integer".to_owned()),
        }
        let text = std::str::from_utf8(&self.input[start..self.position])
            .map_err(|_| "invalid JSON integer bytes".to_owned())?;
        Ok(text.to_owned())
    }

    fn whitespace(&mut self) {
        while matches!(self.peek(), Some(b' ' | b'\t' | b'\n' | b'\r')) {
            self.position += 1;
        }
    }

    fn expect(&mut self, expected: u8) -> Result<(), String> {
        if self.consume(expected) {
            Ok(())
        } else {
            Err(format!("expected JSON byte {:?}", char::from(expected)))
        }
    }

    fn consume(&mut self, expected: u8) -> bool {
        if self.peek() == Some(expected) {
            self.position += 1;
            true
        } else {
            false
        }
    }

    fn peek(&self) -> Option<u8> {
        self.input.get(self.position).copied()
    }

    fn next(&mut self) -> Option<u8> {
        let byte = self.peek()?;
        self.position += 1;
        Some(byte)
    }
}

fn object(value: &Json) -> Result<&[(String, Json)], String> {
    match value {
        Json::Object(members) => Ok(members),
        _ => Err("expected JSON object".to_owned()),
    }
}

fn member<'a>(members: &'a [(String, Json)], name: &str) -> Result<&'a Json, String> {
    let mut matches = members.iter().filter(|(key, _)| key == name);
    let value = matches
        .next()
        .map(|(_, value)| value)
        .ok_or_else(|| format!("missing request member {name}"))?;
    if matches.next().is_some() {
        return Err(format!("duplicate request member {name}"));
    }
    Ok(value)
}

fn exact_keys(members: &[(String, Json)], expected: &[&str]) -> Result<(), String> {
    if members.len() != expected.len()
        || !members
            .iter()
            .all(|(key, _)| expected.iter().any(|candidate| key == candidate))
    {
        return Err("request object has unexpected or duplicate members".to_owned());
    }
    Ok(())
}

fn integer(value: &Json, name: &str) -> Result<i64, String> {
    match value {
        Json::Integer(value) => value
            .parse::<i64>()
            .map_err(|_| format!("{name} is outside the supported profile range")),
        _ => Err(format!("{name} must be a JSON integer")),
    }
}

fn sequence(value: &Json) -> Result<String, String> {
    match value {
        Json::Integer(value) if !value.starts_with('-') => Ok(value.clone()),
        Json::Integer(_) => Err("seq must be nonnegative".to_owned()),
        _ => Err("seq must be a JSON integer".to_owned()),
    }
}

fn sequence_increases(previous: &str, current: &str) -> bool {
    current.len() > previous.len()
        || (current.len() == previous.len() && current.as_bytes() > previous.as_bytes())
}

fn string(value: &Json, name: &str) -> Result<String, String> {
    match value {
        Json::String(value) => Ok(value.clone()),
        _ => Err(format!("{name} must be a JSON string")),
    }
}

#[derive(Debug)]
enum Operation {
    Empty,
    Push { stack: String, value: i64 },
    Pop { stack: String },
}

#[derive(Debug)]
struct Request {
    seq: String,
    operation: Operation,
}

fn decode_request(line: &str) -> Result<Request, String> {
    let document = Parser::new(line).parse()?;
    let request = object(&document)?;
    exact_keys(request, &["seq", "op", "args"])?;

    let seq = sequence(member(request, "seq")?)?;
    let op = string(member(request, "op")?, "op")?;
    let args = object(member(request, "args")?)?;

    let operation = match op.as_str() {
        "empty" => {
            exact_keys(args, &[])?;
            Operation::Empty
        }
        "push" => {
            exact_keys(args, &["stack", "value"])?;
            let stack = string(member(args, "stack")?, "args.stack")?;
            let value = integer(member(args, "value")?, "args.value")?;
            if !(-2..=2).contains(&value) {
                return Err("args.value is outside the selected -2 through 2 domain".to_owned());
            }
            Operation::Push { stack, value }
        }
        "pop" => {
            exact_keys(args, &["stack"])?;
            Operation::Pop {
                stack: string(member(args, "stack")?, "args.stack")?,
            }
        }
        _ => return Err("unsupported v1 operation".to_owned()),
    };

    Ok(Request { seq, operation })
}

struct Session {
    stacks: HashMap<String, Stack>,
    next_handle: u64,
    last_seq: Option<String>,
}

impl Session {
    fn new() -> Self {
        Self {
            stacks: HashMap::new(),
            next_handle: 0,
            last_seq: None,
        }
    }

    fn register(&mut self, stack: Stack) -> String {
        let handle = format!("h{}", self.next_handle);
        self.next_handle += 1;
        self.stacks.insert(handle.clone(), stack);
        handle
    }

    fn respond(&mut self, request: Request) -> String {
        if self
            .last_seq
            .as_deref()
            .is_some_and(|previous| !sequence_increases(previous, &request.seq))
        {
            return error_response(&request.seq, "sequence", "seq must increase monotonically");
        }
        self.last_seq = Some(request.seq.clone());

        match request.operation {
            Operation::Empty => {
                let handle = self.register(Stack::empty());
                stack_response(&request.seq, &handle)
            }
            Operation::Push { stack, value } => {
                let Some(source) = self.stacks.get(&stack).cloned() else {
                    return error_response(&request.seq, "unknown-handle", "stack handle is not live");
                };
                let handle = self.register(source.push(value));
                stack_response(&request.seq, &handle)
            }
            Operation::Pop { stack } => {
                let Some(source) = self.stacks.get(&stack).cloned() else {
                    return error_response(&request.seq, "unknown-handle", "stack handle is not live");
                };
                match source.pop() {
                    None => format!(
                        "{{\"seq\":{},\"status\":\"ok\",\"result\":{{\"tag\":\"none\"}},\"events\":[]}}",
                        request.seq
                    ),
                    Some((value, remainder)) => {
                        let handle = self.register(remainder);
                        format!(
                            "{{\"seq\":{},\"status\":\"ok\",\"result\":{{\"tag\":\"some\",\"value\":{},\"remainder\":\"{}\"}},\"events\":[]}}",
                            request.seq, value, handle
                        )
                    }
                }
            }
        }
    }
}

fn stack_response(seq: &str, handle: &str) -> String {
    format!(
        "{{\"seq\":{seq},\"status\":\"ok\",\"result\":{{\"stack\":\"{handle}\"}},\"events\":[]}}"
    )
}

fn json_string(value: &str) -> String {
    let mut escaped = String::new();
    for character in value.chars() {
        match character {
            '\"' => escaped.push_str("\\\""),
            '\\' => escaped.push_str("\\\\"),
            '\n' => escaped.push_str("\\n"),
            '\r' => escaped.push_str("\\r"),
            '\t' => escaped.push_str("\\t"),
            character if character <= '\u{1f}' => {
                escaped.push_str(&format!("\\u{:04x}", u32::from(character)));
            }
            character => escaped.push(character),
        }
    }
    escaped
}

fn error_response(seq: &str, code: &str, message: &str) -> String {
    format!(
        "{{\"seq\":{seq},\"status\":\"error\",\"error\":{{\"code\":\"{}\",\"message\":\"{}\"}},\"events\":[]}}",
        json_string(code),
        json_string(message)
    )
}

fn run() -> Result<(), String> {
    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut input = stdin.lock();
    let mut output = stdout.lock();
    let mut line = String::new();
    let mut session = Session::new();

    loop {
        line.clear();
        let read = input
            .read_line(&mut line)
            .map_err(|error| format!("cannot read request: {error}"))?;
        if read == 0 {
            return Ok(());
        }
        if !line.ends_with('\n') {
            return Err("request ended without LF framing".to_owned());
        }
        line.pop();

        let request = decode_request(&line)?;
        writeln!(output, "{}", session.respond(request))
            .map_err(|error| format!("cannot write response: {error}"))?;
        output
            .flush()
            .map_err(|error| format!("cannot flush response: {error}"))?;
    }
}

fn main() {
    if let Err(error) = run() {
        eprintln!("stack-rust-adapter: {error}");
        std::process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::{Json, Parser, decode_request};

    #[test]
    fn parser_ignores_order_and_whitespace() {
        let request = decode_request(r#" { "op" : "push", "args" : { "value" : -2, "stack" : "h0" }, "seq" : 7 } "#)
            .expect("valid reordered request");
        assert_eq!("7", request.seq);
    }

    #[test]
    fn parser_preserves_protocol_strings_and_integers() {
        match Parser::new(r#"{"text":"h0","integer":-2}"#)
            .parse()
            .expect("valid JSON")
        {
            Json::Object(members) => assert_eq!(2, members.len()),
            _ => panic!("root was not an object"),
        }
    }
}

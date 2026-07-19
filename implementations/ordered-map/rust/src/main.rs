mod ordered_map;

use ordered_map::OrderedMap;
use std::collections::HashMap;
use std::io::{self, BufRead, Write};

#[derive(Debug)]
enum Json {
    Object(Vec<(String, Json)>),
    String(String),
    Integer(i64),
}

struct Parser<'a> {
    input: &'a [u8],
    position: usize,
}

impl<'a> Parser<'a> {
    fn new(input: &'a str) -> Self {
        Self { input: input.as_bytes(), position: 0 }
    }

    fn parse(mut self) -> Result<Json, String> {
        let value = self.value()?;
        self.whitespace();
        if self.position == self.input.len() {
            Ok(value)
        } else {
            Err("trailing JSON input".to_owned())
        }
    }

    fn value(&mut self) -> Result<Json, String> {
        self.whitespace();
        match self.peek() {
            Some(b'{') => self.object(),
            Some(b'"') => self.string().map(Json::String),
            Some(b'-' | b'0'..=b'9') => self.integer().map(Json::Integer),
            _ => Err("expected JSON value".to_owned()),
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
            members.push((key, self.value()?));
            self.whitespace();
            if self.consume(b'}') {
                return Ok(Json::Object(members));
            }
            self.expect(b',')?;
        }
    }

    fn string(&mut self) -> Result<String, String> {
        self.expect(b'"')?;
        let mut output = Vec::new();
        loop {
            match self.next().ok_or_else(|| "unterminated string".to_owned())? {
                b'"' => return String::from_utf8(output).map_err(|_| "invalid UTF-8".to_owned()),
                b'\\' => match self.next().ok_or_else(|| "short escape".to_owned())? {
                    b'"' => output.push(b'"'),
                    b'\\' => output.push(b'\\'),
                    b'/' => output.push(b'/'),
                    b'b' => output.push(8),
                    b'f' => output.push(12),
                    b'n' => output.push(b'\n'),
                    b'r' => output.push(b'\r'),
                    b't' => output.push(b'\t'),
                    b'u' => {
                        let scalar = self.hex_scalar()?;
                        let character = char::from_u32(scalar)
                            .ok_or_else(|| "invalid Unicode scalar".to_owned())?;
                        let mut bytes = [0_u8; 4];
                        output.extend_from_slice(character.encode_utf8(&mut bytes).as_bytes());
                    }
                    _ => return Err("invalid escape".to_owned()),
                },
                0..=31 => return Err("control byte in string".to_owned()),
                byte => output.push(byte),
            }
        }
    }

    fn hex_scalar(&mut self) -> Result<u32, String> {
        let mut value = 0_u32;
        for _ in 0..4 {
            value = value * 16
                + match self.next().ok_or_else(|| "short Unicode escape".to_owned())? {
                    b'0'..=b'9' => u32::from(self.input[self.position - 1] - b'0'),
                    b'a'..=b'f' => u32::from(self.input[self.position - 1] - b'a') + 10,
                    b'A'..=b'F' => u32::from(self.input[self.position - 1] - b'A') + 10,
                    _ => return Err("invalid Unicode escape".to_owned()),
                };
        }
        Ok(value)
    }

    fn integer(&mut self) -> Result<i64, String> {
        let start = self.position;
        self.consume(b'-');
        match self.peek() {
            Some(b'0') => self.position += 1,
            Some(b'1'..=b'9') => {
                self.position += 1;
                while matches!(self.peek(), Some(b'0'..=b'9')) {
                    self.position += 1;
                }
            }
            _ => return Err("invalid integer".to_owned()),
        }
        let text = std::str::from_utf8(&self.input[start..self.position])
            .map_err(|_| "invalid integer".to_owned())?;
        text.parse().map_err(|_| "integer outside profile".to_owned())
    }

    fn whitespace(&mut self) {
        while matches!(self.peek(), Some(b' ' | b'\t' | b'\n' | b'\r')) {
            self.position += 1;
        }
    }

    fn expect(&mut self, byte: u8) -> Result<(), String> {
        if self.consume(byte) { Ok(()) } else { Err("unexpected JSON byte".to_owned()) }
    }

    fn consume(&mut self, byte: u8) -> bool {
        if self.peek() == Some(byte) {
            self.position += 1;
            true
        } else {
            false
        }
    }

    fn peek(&self) -> Option<u8> { self.input.get(self.position).copied() }
    fn next(&mut self) -> Option<u8> {
        let byte = self.peek()?;
        self.position += 1;
        Some(byte)
    }
}

fn object(value: &Json) -> Result<&[(String, Json)], String> {
    match value { Json::Object(value) => Ok(value), _ => Err("expected object".to_owned()) }
}

fn exact(members: &[(String, Json)], keys: &[&str]) -> Result<(), String> {
    if members.len() == keys.len()
        && members.iter().all(|(name, _)| keys.contains(&name.as_str()))
        && keys.iter().all(|key| members.iter().filter(|(name, _)| name == key).count() == 1)
    {
        Ok(())
    } else {
        Err("unexpected members".to_owned())
    }
}

fn member<'a>(members: &'a [(String, Json)], key: &str) -> Result<&'a Json, String> {
    members.iter().find(|(name, _)| name == key).map(|(_, value)| value)
        .ok_or_else(|| "missing member".to_owned())
}

fn string(value: &Json) -> Result<&str, String> {
    match value { Json::String(value) if !value.is_empty() => Ok(value), _ => Err("expected string".to_owned()) }
}

fn integer(value: &Json) -> Result<i64, String> {
    match value { Json::Integer(value) if (-2..=2).contains(value) => Ok(*value), _ => Err("value outside profile".to_owned()) }
}

enum Operation {
    Empty,
    Put { map: String, key: String, value: i64 },
    Lookup { map: String, key: String },
    Entries { map: String },
}

struct Request { seq: i64, operation: Operation }

fn request(line: &str, expected_seq: i64) -> Result<Request, String> {
    let document = Parser::new(line).parse()?;
    let root = object(&document)?;
    exact(root, &["seq", "op", "args"])?;
    let seq = match member(root, "seq")? { Json::Integer(value) => *value, _ => return Err("seq must be integer".to_owned()) };
    if seq != expected_seq { return Err("sequence mismatch".to_owned()); }
    let op = string(member(root, "op")?)?;
    let args = object(member(root, "args")?)?;
    let operation = match op {
        "empty" => { exact(args, &[])?; Operation::Empty }
        "put" => {
            exact(args, &["map", "key", "value"])?;
            Operation::Put {
                map: string(member(args, "map")?)?.to_owned(),
                key: string(member(args, "key")?)?.to_owned(),
                value: integer(member(args, "value")?)?,
            }
        }
        "lookup" => {
            exact(args, &["map", "key"])?;
            Operation::Lookup {
                map: string(member(args, "map")?)?.to_owned(),
                key: string(member(args, "key")?)?.to_owned(),
            }
        }
        "entries" => {
            exact(args, &["map"])?;
            Operation::Entries { map: string(member(args, "map")?)?.to_owned() }
        }
        _ => return Err("unknown operation".to_owned()),
    };
    Ok(Request { seq, operation })
}

struct Session { maps: HashMap<String, OrderedMap>, next_handle: u64 }

impl Session {
    fn new() -> Self { Self { maps: HashMap::new(), next_handle: 0 } }

    fn store(&mut self, map: OrderedMap) -> String {
        let handle = format!("rust-map-{}", self.next_handle);
        self.next_handle += 1;
        self.maps.insert(handle.clone(), map);
        handle
    }

    fn retained(&self, handle: &str) -> Result<OrderedMap, String> {
        self.maps.get(handle).cloned().ok_or_else(|| "unknown map handle".to_owned())
    }

    fn execute(&mut self, request: Request) -> Result<String, String> {
        let result = match request.operation {
            Operation::Empty => format!("{{\"map\":\"{}\"}}", self.store(OrderedMap::empty())),
            Operation::Put { map, key, value } => {
                let updated = self.retained(&map)?.put(&key, value)?;
                format!("{{\"map\":\"{}\"}}", self.store(updated))
            }
            Operation::Lookup { map, key } => match self.retained(&map)?.lookup(&key)? {
                Some(value) => format!("{{\"tag\":\"some\",\"value\":{value}}}"),
                None => "{\"tag\":\"none\"}".to_owned(),
            },
            Operation::Entries { map } => {
                let retained = self.retained(&map)?;
                let entries = retained.entries().iter().map(|(token, value)| {
                    format!("{{\"class\":\"{}\",\"value\":{value}}}", token.as_str())
                }).collect::<Vec<_>>().join(",");
                format!("{{\"entries\":[{entries}]}}")
            }
        };
        Ok(format!("{{\"seq\":{},\"status\":\"ok\",\"result\":{},\"events\":[]}}", request.seq, result))
    }
}

fn main() {
    let stdin = io::stdin();
    let mut stdout = io::stdout().lock();
    let mut session = Session::new();
    let mut sequence = 0_i64;
    for line in stdin.lock().lines() {
        let response = line
            .map_err(|error| error.to_string())
            .and_then(|line| request(&line, sequence))
            .and_then(|request| session.execute(request));
        match response {
            Ok(response) => {
                writeln!(stdout, "{response}").unwrap();
                stdout.flush().unwrap();
                sequence += 1;
            }
            Err(error) => {
                eprintln!("invalid bounded request: {error}");
                std::process::exit(2);
            }
        }
    }
}

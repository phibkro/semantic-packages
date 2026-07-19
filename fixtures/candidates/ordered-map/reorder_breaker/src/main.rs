mod ordered_map;

use ordered_map::OrderedMap;
use std::collections::HashMap;
use std::io::{self, BufRead, Write};

enum Operation {
    Empty,
    Put { map: String, key: String, value: i64 },
    Lookup { map: String, key: String },
    Entries { map: String },
}

struct Request {
    seq: i64,
    operation: Operation,
}

fn integer_after(line: &str, marker: &str) -> Result<i64, String> {
    let start = line.find(marker).ok_or_else(|| "missing integer".to_owned())?
        + marker.len();
    let tail = &line[start..];
    let end = tail
        .find(|character: char| character == ',' || character == '}')
        .unwrap_or(tail.len());
    tail[..end]
        .parse::<i64>()
        .map_err(|_| "invalid integer".to_owned())
}

fn string_after(line: &str, marker: &str) -> Result<String, String> {
    let start = line.find(marker).ok_or_else(|| "missing string".to_owned())?
        + marker.len();
    let tail = &line[start..];
    let end = tail.find('"').ok_or_else(|| "unterminated string".to_owned())?;
    Ok(tail[..end].to_owned())
}

fn request(line: &str, expected_seq: i64) -> Result<Request, String> {
    let seq = integer_after(line, "{\"seq\":")?;
    if seq != expected_seq {
        return Err("sequence mismatch".to_owned());
    }
    let op = string_after(line, "\"op\":\"")?;
    let operation = match op.as_str() {
        "empty" => Operation::Empty,
        "put" => Operation::Put {
            map: string_after(line, "\"map\":\"")?,
            key: string_after(line, "\"key\":\"")?,
            value: integer_after(line, "\"value\":" )?,
        },
        "lookup" => Operation::Lookup {
            map: string_after(line, "\"map\":\"")?,
            key: string_after(line, "\"key\":\"")?,
        },
        "entries" => Operation::Entries {
            map: string_after(line, "\"map\":\"")?,
        },
        _ => return Err("unknown operation".to_owned()),
    };
    Ok(Request { seq, operation })
}

struct Session {
    maps: HashMap<String, OrderedMap>,
    next_handle: u64,
}

impl Session {
    fn new() -> Self {
        Self { maps: HashMap::new(), next_handle: 0 }
    }

    fn store(&mut self, map: OrderedMap) -> String {
        let handle = format!("breaker-map-{}", self.next_handle);
        self.next_handle += 1;
        self.maps.insert(handle.clone(), map);
        handle
    }

    fn retained(&self, handle: &str) -> Result<OrderedMap, String> {
        self.maps
            .get(handle)
            .cloned()
            .ok_or_else(|| "unknown handle".to_owned())
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
                let entries = retained
                    .entries()
                    .iter()
                    .map(|(token, value)| {
                        format!("{{\"class\":\"{}\",\"value\":{value}}}", token.as_str())
                    })
                    .collect::<Vec<_>>()
                    .join(",");
                format!("{{\"entries\":[{entries}]}}")
            }
        };
        Ok(format!(
            "{{\"seq\":{},\"status\":\"ok\",\"result\":{},\"events\":[]}}",
            request.seq, result
        ))
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

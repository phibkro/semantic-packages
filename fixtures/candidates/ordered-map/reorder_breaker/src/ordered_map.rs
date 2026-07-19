#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ClassToken {
    A,
    B,
    C,
}

impl ClassToken {
    pub fn from_key(key: &str) -> Result<Self, String> {
        match key {
            "A" | "a" => Ok(Self::A),
            "B" | "b" => Ok(Self::B),
            "C" | "c" => Ok(Self::C),
            _ => Err("key outside bounded domain".to_owned()),
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            Self::A => "a",
            Self::B => "b",
            Self::C => "c",
        }
    }
}

#[derive(Clone)]
pub struct OrderedMap {
    entries: Vec<(ClassToken, i64)>,
}

impl OrderedMap {
    pub fn empty() -> Self {
        Self { entries: Vec::new() }
    }

    pub fn put(&self, key: &str, value: i64) -> Result<Self, String> {
        let token = ClassToken::from_key(key)?;
        let mut entries = self.entries.clone();
        if let Some(position) = entries.iter().position(|(item, _)| *item == token) {
            entries.remove(position);
        }
        entries.push((token, value));
        Ok(Self { entries })
    }

    pub fn lookup(&self, key: &str) -> Result<Option<i64>, String> {
        let token = ClassToken::from_key(key)?;
        Ok(self
            .entries
            .iter()
            .find(|(item, _)| *item == token)
            .map(|(_, value)| *value))
    }

    pub fn entries(&self) -> &[(ClassToken, i64)] {
        &self.entries
    }
}

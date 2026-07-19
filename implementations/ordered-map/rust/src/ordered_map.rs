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
            _ => Err("key is outside the selected profile domain".to_owned()),
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

#[derive(Clone, Debug, Eq, PartialEq)]
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
            entries[position].1 = value;
        } else {
            entries.push((token, value));
        }
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

#[cfg(test)]
mod tests {
    use super::OrderedMap;

    #[test]
    fn replacement_retains_position_and_sources() {
        let empty = OrderedMap::empty();
        let one = empty.put("A", 1).unwrap();
        let two = one.put("B", 2).unwrap();
        let replaced = two.put("a", -1).unwrap();

        assert_eq!(None, empty.lookup("a").unwrap());
        assert_eq!(Some(1), one.lookup("A").unwrap());
        assert_eq!([("a", -1), ("b", 2)], visible(&replaced)[..]);
        assert_eq!([("a", 1), ("b", 2)], visible(&two)[..]);
    }

    fn visible(map: &OrderedMap) -> Vec<(&'static str, i64)> {
        map.entries()
            .iter()
            .map(|(token, value)| (token.as_str(), *value))
            .collect()
    }
}

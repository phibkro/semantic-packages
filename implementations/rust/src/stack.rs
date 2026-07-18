/// A finite persistent Stack realization.
///
/// Values are stored bottom-first in an immutable boxed slice. Operations allocate a
/// new slice and never mutate the source Stack, so every retained value remains usable.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Stack {
    values: Box<[i64]>,
}

impl Stack {
    pub fn empty() -> Self {
        Self {
            values: Box::new([]),
        }
    }

    pub fn push(&self, value: i64) -> Self {
        let mut values = Vec::with_capacity(self.values.len() + 1);
        values.extend_from_slice(&self.values);
        values.push(value);
        Self {
            values: values.into_boxed_slice(),
        }
    }

    pub fn pop(&self) -> Option<(i64, Self)> {
        let (&value, remainder) = self.values.split_last()?;
        Some((
            value,
            Self {
                values: remainder.to_vec().into_boxed_slice(),
            },
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::Stack;

    #[test]
    fn operations_leave_sources_unchanged() {
        let empty = Stack::empty();
        let one = empty.push(1);
        let two = one.push(2);

        assert_eq!(None, empty.pop());
        assert_eq!(Some((1, Stack::empty())), one.pop());
        assert_eq!(Some((2, one.clone())), two.pop());
        assert_eq!(Some((1, Stack::empty())), one.pop());
    }
}

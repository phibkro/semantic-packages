use std::rc::Rc;

/// A persistent Stack implementation used only by this negative-control fixture.
#[derive(Clone, Default)]
pub struct Stack(Option<Rc<Node>>);

struct Node {
    value: i64,
    previous: Stack,
}

impl Stack {
    pub fn empty() -> Self {
        Self::default()
    }

    pub fn push(&self, value: i64) -> Self {
        Self(Some(Rc::new(Node {
            value,
            previous: self.clone(),
        })))
    }

    pub fn pop(&self) -> Option<(i64, Self)> {
        self.0
            .as_ref()
            .map(|node| (node.value, node.previous.clone()))
    }
}

from dataclasses import dataclass

import streamlit as st


@dataclass
class Progress_bar:
    total: int
    current: int = 0

    def update(self, step: int = 1):
        self.current += step
        self.display()

    def display(self):
        assert self.total > 0, "Total must be greater than zero"
        progress = self.current / self.total
        print(f"Progress: {progress}%")
        st.progress(progress)

import attr


@attr.s
class Experiment:
    label = attr.ib()


@attr.s
class Result:
    label = attr.ib()


@attr.s
class Interaction:
    label = attr.ib()
    experience = attr.ib(None)
    result = attr.ib(None)
    valence = attr.ib(None)


@attr.s
class Existence:
    mood = attr.ib(None)
    experiences = attr.ib(factory=dict)
    interactions = attr.ib(factory=dict)
    results = attr.ib(factory=dict)

    def __attrs_post_init__(self):
        e1 = self.get_experience('e1')
        e2 = self.get_experience('e2')
        r1 = self.get_result('r1')
        r2 = self.get_result('r2')
        self.setup_interaction(e1, r1, -1)
        self.setup_interaction(e1, r2, 1)
        self.setup_interaction(e2, r1, -1)
        self.setup_interaction(e2, r2, 1)
        self.prev_experience = e1

    def get_experience(self, label: str) -> Experiment:
        if label not in self.experiences:
            self.experiences[label] = Experiment(label)
        return self.experiences[label]

    def get_result(self, label: str) -> Result:
        if label not in self.results:
            self.results[label] = Result(label)
        return self.results[label]

    def get_interaction(self, label: str) -> Interaction:
        if label not in self.interactions:
            self.interactions[label] = Interaction(label)
        return self.interactions[label]

    def swap_experience(self, experience: Experiment) -> Experiment:
        for e in self.experiences.values():
            if e != experience:
                return e

    def create_result(self, experience: Experiment) -> Result:
        if experience == self.get_experience('e1'):
            return self.get_result('r1')
        return self.get_result('r2')

    def setup_interaction(self, experience: Experiment, result: Result, valence: int = None) -> Interaction:
        interaction = self.get_interaction(experience.label + result.label)
        interaction.experience = experience
        interaction.result = result
        if valence:
            interaction.valence = valence
        return interaction

    def predict_result(self, experience: Experiment) -> Result:
        for i in self.interactions.values():
            if i.experience == experience:
                return i.result
        return None

    def step(self) -> str:
        experience = self.prev_experience

        if self.mood == 'pained':
            experience = self.swap_experience(experience)

        result = self.create_result(experience)
        interaction = self.setup_interaction(experience, result)

        if interaction.valence > 0:
            self.mood = 'pleased'
        else:
            self.mood = 'pained'

        self.prev_experience = experience

        return f'{experience.label}{result.label} {self.mood}'


if __name__ == '__main__':
    existence = Existence()

    for i in range(20):
        trace = existence.step()
        print(f'{i:02d}: {trace}')

import attr


@attr.s
class Experiment:
    label = attr.ib()


@attr.s
class Result:
    label = attr.ib()


@attr.s
class Interaction:
    experiment = attr.ib()
    result = attr.ib()
    valence = attr.ib()

    @property
    def label(self):
        return self.experiment.label + self.result.label


@attr.s
class Environment:
    results = dict()

    def get_result(self, label: str) -> Result:
        return self.results.setdefault(label, Result(label))

    def perform(self, experiment: Experiment) -> Result:
        if experiment == Experiment("e1"):
            return self.get_result("r1")
        return self.get_result("r2")


@attr.s
class Existence:
    env = attr.ib()

    mood = None
    experience = None
    experiments = dict()
    interactions = dict()

    def __attrs_post_init__(self):
        e1 = self.get_experiment("e1")
        e2 = self.get_experiment("e2")
        r1 = self.env.get_result("r1")
        r2 = self.env.get_result("r2")
        self.get_interaction(e1, r1, -1)
        self.get_interaction(e1, r2, 1)
        self.get_interaction(e2, r1, -1)
        self.get_interaction(e2, r2, 1)
        self.experience = e1

    def get_experiment(self, label: str) -> Experiment:
        return self.experiments.setdefault(label, Experiment(label))

    def get_interaction(
        self, experiment: Experiment, result: Result, valence: int
    ) -> Interaction:
        interaction = Interaction(experiment, result, valence)
        return self.interactions.setdefault(interaction.label, interaction)

    def swap(self, experiment: Experiment) -> Experiment:
        for e in self.experiments.values():
            if e != experiment:
                return e

    def find(self, experiment: Experiment, result: Result) -> Interaction:
        for i in self.interactions.values():
            if i.experiment == experiment and i.result == result:
                return i

    def step(self) -> str:
        experiment = self.experience

        if self.mood == "pained":
            experiment = self.swap(experiment)

        result = self.env.perform(experiment)
        interaction = self.find(experiment, result)

        if interaction.valence > 0:
            self.mood = "pleased"
        else:
            self.mood = "pained"

        self.experience = experiment

        return f"{interaction.label} {self.mood}"


if __name__ == "__main__":
    env = Environment()
    existence = Existence(env)

    for i in range(20):
        trace = existence.step()
        print(f"{i:02d}: {trace}")

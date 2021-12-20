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

    @property
    def label(self):
        return self.experiment.label + self.result.label


@attr.s
class Environment:
    def perform(self, experiment: Experiment) -> Result:
        if experiment == Experiment("e1"):
            return Result("r1")
        return Result("r2")


@attr.s
class Existence:
    env = attr.ib()

    mood = None
    experience = None
    experiments = dict()
    interactions = dict()
    satisfaction = 0

    def __attrs_post_init__(self):
        self.experience = self.get_experiment("e1")
        self.get_experiment("e2")

    def get_experiment(self, label: str) -> Experiment:
        return self.experiments.setdefault(label, Experiment(label))

    def get_interaction(self, experiment: Experiment, result: Result) -> Interaction:
        interaction = Interaction(experiment, result)
        return self.interactions.setdefault(interaction.label, interaction)

    def swap(self, experiment: Experiment) -> Experiment:
        for e in self.experiments.values():
            if e != experiment:
                return e

    def predict(self, experiment: Experiment) -> Result:
        for i in self.interactions.values():
            if i.experiment == experiment:
                return i.result
        return None

    def step(self) -> str:
        experiment = self.experience

        if self.mood == "bored":
            experiment = self.swap(experiment)
            self.satisfaction = 0

        anticipated = self.predict(experiment)
        result = self.env.perform(experiment)

        interaction = self.get_interaction(experiment, result)

        if anticipated == result:
            self.mood = "satisfied"
            self.satisfaction += 1
        else:
            self.mood = "frustrated"
            self.satisfaction = 0

        if self.satisfaction > 4:
            self.mood = "bored"

        self.experience = experiment

        return f"{interaction.label} {self.mood}"


if __name__ == "__main__":
    env = Environment()
    existence = Existence(env)

    for i in range(20):
        trace = existence.step()
        print(f"{i:02d}: {trace}")

import attr
import typing


@attr.s
class Experiment:
    label = attr.ib()


@attr.s
class Result:
    label = attr.ib()


@attr.s
class Interaction:
    pass


@attr.s
class PrimitiveInteraction(Interaction):
    experiment = attr.ib()
    result = attr.ib()
    valence = attr.ib()

    @property
    def label(self):
        return self.experiment.label + self.result.label


@attr.s
class CompositeInteraction(Interaction):
    anterior = attr.ib()
    posterior = attr.ib()

    @property
    def label(self):
        return self.anterior.label + self.posterior.label

    @property
    def valence(self):
        return self.anterior.valence + self.posterior.valence


@attr.s
class Anticipation:
    interaction = attr.ib(eq=lambda x: x.valence)


@attr.s
class Environment:
    results = dict()
    experiment = None

    def get_result(self, label: str) -> Experiment:
        return self.results.setdefault(label, Experiment(label))

    def perform(self, experiment: Experiment) -> Result:
        if self.experiment == experiment:
            return self.get_result("r1")
        self.experiment = experiment
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
        self.get_primitive_interaction(e1, r1, -1)
        self.get_primitive_interaction(e1, r2, 1)
        self.get_primitive_interaction(e2, r1, -1)
        self.get_primitive_interaction(e2, r2, 1)

    def get_experiment(self, label: str) -> Experiment:
        return self.experiments.setdefault(label, Experiment(label))

    def get_primitive_interaction(
        self, experiment: Experiment, result: Result, valence: int
    ) -> Interaction:
        interaction = PrimitiveInteraction(experiment, result, valence)
        return self.interactions.setdefault(interaction.label, interaction)

    def get_composite_interaction(
        self, anterior: Interaction, posterior: Interaction
    ) -> Interaction:
        interaction = CompositeInteraction(anterior, posterior)
        self.interactions[interaction.label] = interaction
        print(f"learn: {interaction.label} | {interaction.valence}")
        return interaction

    def swap(self, interaction: typing.Optional[Interaction]) -> Interaction:
        if interaction is None:
            return list(self.interactions.values())[0]

        for i in self.interactions.values():
            if (
                isinstance(i, PrimitiveInteraction)
                and i.experiment != interaction.experiment
            ):
                return i

    def get_active(self, experience: Interaction) -> typing.List[Interaction]:
        interactions = []
        for i in self.interactions.values():
            if isinstance(i, CompositeInteraction) and i.anterior == experience:
                print(f"activated: {i.label}")
                interactions.append(i)
        return interactions

    def anticipate(self, experience: Interaction) -> typing.List[Anticipation]:
        anticipations = []
        for i in self.get_active(experience):
            interaction = i.posterior
            anticipations.append(Anticipation(interaction))
            print(f"afforded: {interaction.label} | {interaction.valence}")
        return anticipations

    def select(self, anticipations: typing.List[Anticipation]) -> Interaction:
        anticipations = list(reversed(sorted(anticipations)))

        if len(anticipations):
            interaction = anticipations[0].interaction
            if interaction.valence >= 0:
                return interaction
            return self.swap(interaction)
        return self.swap(None)

    def find(self, experiment: Experiment, result: Result) -> Interaction:
        for i in self.interactions.values():
            if (
                isinstance(i, PrimitiveInteraction)
                and i.experiment == experiment
                and i.result == result
            ):
                return i

    def step(self) -> str:
        anticipations = self.anticipate(self.experience)
        experiment = self.select(anticipations).experiment

        result = self.env.perform(experiment)
        interaction = self.find(experiment, result)
        print(f"enacted: {interaction.label} | {interaction.valence}")

        if interaction.valence > 0:
            self.mood = "pleased"
        else:
            self.mood = "pained"

        if self.experience is not None:
            self.get_composite_interaction(self.experience, interaction)

        self.experience = interaction

        return self.mood


if __name__ == "__main__":
    env = Environment()
    existence = Existence(env)

    for i in range(20):
        trace = existence.step()
        print(f"{i:02d}: {trace}")
        print(15 * "-")

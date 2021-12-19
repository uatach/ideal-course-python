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
    weight = attr.ib()

    @property
    def label(self):
        return self.anterior.label + self.posterior.label

    @property
    def valence(self):
        return self.anterior.valence + self.posterior.valence


@attr.s
class Anticipation:
    experiment = attr.ib(order=False)
    proclivity = attr.ib()


@attr.s
class Environment:
    results = dict()
    experiment = None
    clock = 0

    def get_result(self, label: str) -> Experiment:
        return self.results.setdefault(label, Experiment(label))

    def perform(self, experiment: Experiment) -> Result:
        self.clock += 1
        if self.clock <= 8 or self.clock > 15:
            if experiment == Experiment('e1'):
                return self.get_result("r1")
            return self.get_result("r2")

        if experiment == Experiment('e1'):
            return self.get_result("r2")
        return self.get_result("r1")


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

    def get_composite_interaction(self, anterior: Interaction, posterior: Interaction, weight: int) -> Interaction:
        interaction = CompositeInteraction(anterior, posterior, weight)
        self.interactions[interaction.label] = interaction
        print(f'learn: {interaction.label} | {interaction.valence} | {interaction.weight}')
        return interaction

    def get_active(self, experience: Interaction) -> typing.List[Interaction]:
        interactions = []
        for i in self.interactions.values():
            if isinstance(i, CompositeInteraction) and i.anterior == experience:
                print(f'activated: {i.label}')
                interactions.append(i)
        return interactions

    def anticipate(self, experience: Interaction) -> typing.List[Anticipation]:
        anticipations = [Anticipation(e, 0) for e in self.experiments.values()]
        for i in self.get_active(experience):
            proclivity = i.weight * i.posterior.valence
            proposition = Anticipation(i.posterior.experiment, proclivity)
            for a in anticipations:
                if a.experiment == proposition.experiment:
                    a.proclivity = proposition.proclivity
        return anticipations

    def select(self, anticipations: typing.List[Anticipation]) -> Interaction:
        anticipations = list(sorted(anticipations, reverse=True))

        for a in anticipations:
            print(f'propose: {a.experiment.label} | {a.proclivity}')
        return anticipations[0].experiment

    def find_primitive(self, experiment: Experiment, result: Result) -> Interaction:
        for i in self.interactions.values():
            if isinstance(i, PrimitiveInteraction) and i.experiment == experiment and i.result == result:
                return i

    def find_composite(self, anterior: Interaction, posterior: Interaction) -> Interaction:
        for i in self.interactions.values():
            if isinstance(i, CompositeInteraction) and i.anterior == anterior and i.posterior == posterior:
                i.weight += 1
                return i
        return self.get_composite_interaction(anterior, posterior, 1)

    def step(self) -> str:
        anticipations = self.anticipate(self.experience)
        experiment = self.select(anticipations)

        result = self.env.perform(experiment)
        interaction = self.find_primitive(experiment, result)
        print(f'enacted: {interaction.label} | {interaction.valence}')

        if interaction.valence > 0:
            self.mood = 'pleased'
        else:
            self.mood = 'pained'

        if self.experience is not None:
            self.find_composite(self.experience, interaction)

        self.experience = interaction

        return self.mood


if __name__ == "__main__":
    env = Environment()
    existence = Existence(env)

    for i in range(20):
        trace = existence.step()
        print(f"{i:02d}: {trace}")
        print(15 * '-')

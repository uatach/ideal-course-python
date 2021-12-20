import attr
import typing


@attr.s
class Experiment:
    label = attr.ib()
    interaction = attr.ib(None)
    abstract = attr.ib(True)


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
    experiment = None

    @property
    def label(self):
        return f"<{self.anterior.label}{self.posterior.label}>"

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
    experiments = [None, None, None]

    def get_result(self, label: str) -> Result:
        return self.results.setdefault(label, Result(label))

    def perform(self, experiment: Experiment) -> Result:
        result = self.get_result("r1")
        if (
            self.experiments[0] != experiment
            and self.experiments[1] == experiment
            and self.experiments[2] == experiment
        ):
            result = self.get_result("r2")

        self.experiments = self.experiments[1:] + [experiment]
        return result


@attr.s
class Existence:
    env = attr.ib()

    mood = None
    memory = (None, None)
    experiments = dict()
    interactions = dict()

    def __attrs_post_init__(self):
        e1 = self.get_experiment("e1")
        e2 = self.get_experiment("e2")
        r1 = self.env.get_result("r1")
        r2 = self.env.get_result("r2")
        i11 = self.get_primitive_interaction(e1, r1, -1)
        i12 = self.get_primitive_interaction(e1, r2, 1)
        i21 = self.get_primitive_interaction(e2, r1, -1)
        i22 = self.get_primitive_interaction(e2, r2, 1)
        e1.interaction = i12
        e2.interaction = i22
        e1.abstract = False
        e2.abstract = False

    def get_experiment(self, label: str) -> Experiment:
        return self.experiments.setdefault(label, Experiment(label))

    def get_abstract_experiment(self, interaction: Interaction) -> Experiment:
        label = interaction.label.replace("e", "E").replace("r", "R").replace(">", "|")
        experiment = self.get_experiment(label)
        experiment.interaction = interaction
        interaction.experiment = experiment
        return experiment

    def get_primitive_interaction(
        self, experiment: Experiment, result: Result, valence: int
    ) -> Interaction:
        interaction = PrimitiveInteraction(experiment, result, valence)
        return self.interactions.setdefault(interaction.label, interaction)

    def get_composite_interaction(
        self, anterior: Interaction, posterior: Interaction, weight: int
    ) -> Interaction:
        interaction = CompositeInteraction(anterior, posterior, weight)
        self.get_abstract_experiment(interaction)
        self.interactions[interaction.label] = interaction
        print(
            f"learn: {interaction.label} | {interaction.valence} | {interaction.weight}"
        )
        return interaction

    def get_active(
        self, experiences: typing.List[Interaction]
    ) -> typing.List[Interaction]:
        context = []
        if experiences[0] is not None:
            context.append(experiences[0])

        if experiences[1] is not None:
            context.append(experiences[1])

        if isinstance(experiences[1], CompositeInteraction):
            context.append(experiences[1].posterior)

        interactions = []
        for i in self.interactions.values():
            if isinstance(i, CompositeInteraction) and i.anterior in context:
                print(f"activated: {i.label}")
                interactions.append(i)
        return interactions

    def anticipate(
        self, interactions: typing.List[Interaction]
    ) -> typing.List[Anticipation]:
        anticipations = [
            Anticipation(e, 0) for e in self.experiments.values() if not e.abstract
        ]
        for i in interactions:
            proclivity = i.weight * i.posterior.valence
            proposition = Anticipation(i.posterior.experiment, proclivity)
            append = True
            for a in anticipations:
                if a.experiment == proposition.experiment:
                    a.proclivity += proposition.proclivity
                    append = False
            if append:
                anticipations.append(proposition)
        return anticipations

    def select(self, anticipations: typing.List[Anticipation]) -> Interaction:
        anticipations = list(sorted(anticipations, reverse=True))

        for a in anticipations[:5]:
            print(f"propose: {a.experiment.label} | {a.proclivity}")
        return anticipations[0].experiment

    def find_primitive(self, experiment: Experiment, result: Result) -> Interaction:
        for i in self.interactions.values():
            if (
                isinstance(i, PrimitiveInteraction)
                and i.experiment == experiment
                and i.result == result
            ):
                return i
        return self.get_primitive_interaction(experiment, result, -1)

    def find_composite(
        self, anterior: Interaction, posterior: Interaction
    ) -> Interaction:
        for i in self.interactions.values():
            if (
                isinstance(i, CompositeInteraction)
                and i.anterior == anterior
                and i.posterior == posterior
            ):
                i.weight += 1
                print(f"reinforce: {i.label} | {i.valence} | {i.weight}")
                return i
        return self.get_composite_interaction(anterior, posterior, 1)

    def enact_primitive(self, interaction: Interaction) -> Interaction:
        experiment = interaction.experiment
        result = self.env.perform(experiment)
        return self.find_primitive(experiment, result)

    def enact_composite(self, interaction: Interaction) -> Interaction:
        if isinstance(interaction, PrimitiveInteraction):
            return self.enact_primitive(interaction)

        anterior = self.enact_composite(interaction.anterior)
        if anterior != interaction.anterior:
            return anterior

        posterior = self.enact_composite(interaction.posterior)
        return self.find_composite(anterior, posterior)

    def step(self) -> str:
        interactions = self.get_active(self.memory)
        anticipations = self.anticipate(interactions)
        experiment = self.select(anticipations)

        intended = experiment.interaction
        enacted = self.enact_composite(intended)
        print(f"enacted: {enacted.label} | {enacted.valence}")

        if intended != enacted and experiment.abstract:
            result = self.env.get_result(
                enacted.label.replace("e", "E").replace("r", "R") + ">"
            )
            valence = enacted.valence
            enacted = self.get_primitive_interaction(experiment, result, valence)

        if enacted.valence >= 0:
            self.mood = "pleased"
        else:
            self.mood = "pained"

        experience = None

        if self.memory[1] is not None:
            experience = self.find_composite(self.memory[1], enacted)

        if self.memory[0] is not None:
            self.find_composite(self.memory[0].anterior, experience)
            self.find_composite(self.memory[0], enacted)

        self.memory = (experience, enacted)

        return self.mood


if __name__ == "__main__":
    env = Environment()
    existence = Existence(env)

    for i in range(26):
        trace = existence.step()
        print(f"{i:02d}: {trace}")
        print(15 * "-")

import attr
import typing


@attr.s
class Experiment:
    intended = attr.ib()
    enacted = None

    def __attrs_post_init__(self):
        self.enacted = list()

    @property
    def label(self):
        return self.intended.label.replace("e", "E").replace("r", "R").replace(">", "|")


@attr.s
class Interaction:
    pass


@attr.s
class PrimitiveInteraction(Interaction):
    label = attr.ib()
    valence = attr.ib()


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
    interactions = dict()
    history = [None, None]

    def get_interaction(self, label: str, valence: int = 0) -> Interaction:
        return self.interactions.setdefault(label, PrimitiveInteraction(label, valence))

    def perform(self, intended: Interaction) -> Interaction:
        enacted = None

        if "e1" in intended.label:
            if (
                self.history[1] is not None
                and "e1" in self.history[1].label
                and (self.history[0] is None or "e2" in self.history[0].label)
            ):
                enacted = self.get_interaction("e1r2")
            else:
                enacted = self.get_interaction("e1r1")
        else:
            if (
                self.history[1] is not None
                and "e2" in self.history[1].label
                and (self.history[0] is None or "e1" in self.history[0].label)
            ):
                enacted = self.get_interaction("e2r2")
            else:
                enacted = self.get_interaction("e2r1")

        self.history = [self.history[1], enacted]
        return enacted


@attr.s
class Existence:
    env = attr.ib()

    mood = None
    memory = (None, None)
    experiments = dict()
    interactions = dict()

    def __attrs_post_init__(self):
        i11 = self.env.get_interaction("e1r1", -1)
        i12 = self.env.get_interaction("e1r2", 3)
        i21 = self.env.get_interaction("e2r1", -1)
        i22 = self.env.get_interaction("e2r2", 3)
        self.get_abstract_experiment(i12)
        self.get_abstract_experiment(i22)

    def get_experiment(self, interaction: Interaction) -> Experiment:
        experiment = Experiment(interaction)
        return self.experiments.setdefault(experiment.label, experiment)

    def get_abstract_experiment(self, interaction: Interaction) -> Experiment:
        experiment = self.get_experiment(interaction)
        interaction.experiment = experiment
        return experiment

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
                interactions.append(i)
        return interactions

    def anticipate(
        self, interactions: typing.List[Interaction]
    ) -> typing.List[Anticipation]:

        anticipations = [
            Anticipation(e, 0)
            for e in self.experiments.values()
            if isinstance(e.intended, PrimitiveInteraction)
        ]

        for interaction in interactions:
            if isinstance(interaction.posterior, CompositeInteraction):
                proclivity = interaction.weight * interaction.posterior.valence
                proposition = Anticipation(interaction.posterior.experiment, proclivity)
                append = True
                for anticipation in anticipations:
                    if anticipation.experiment == proposition.experiment:
                        anticipation.proclivity += proposition.proclivity
                        append = False
                if append:
                    anticipations.append(proposition)

        for anticipation in anticipations:
            for enacted in anticipation.experiment.enacted:
                for interaction in interactions:
                    if enacted == interaction.posterior:
                        proclivity = interaction.weight * enacted.valence
                        anticipation.proclivity += proclivity

        return anticipations

    def select(self, anticipations: typing.List[Anticipation]) -> Interaction:
        anticipations = list(sorted(anticipations, reverse=True))

        for a in anticipations[:5]:
            print(f"propose: {a.experiment.label} | {a.proclivity}")
        return anticipations[0].experiment

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

    def enact_composite(self, interaction: Interaction) -> Interaction:
        if isinstance(interaction, PrimitiveInteraction):
            return self.env.perform(interaction)

        anterior = self.enact_composite(interaction.anterior)
        if anterior != interaction.anterior:
            return anterior

        posterior = self.enact_composite(interaction.posterior)
        return self.find_composite(anterior, posterior)

    def step(self) -> str:
        interactions = self.get_active(self.memory)
        anticipations = self.anticipate(interactions)
        experiment = self.select(anticipations)

        intended = experiment.intended
        print(f"intended: {intended.label} | {intended.valence}")

        enacted = self.enact_composite(intended)
        print(f"enacted: {enacted.label} | {enacted.valence}")

        if intended != enacted:
            experiment.enacted.append(enacted)

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

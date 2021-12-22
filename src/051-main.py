import attr
import typing

from time import sleep


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

    agent_icons = '^>v<'
    agent_position = (4, 1)
    agent_orientation = 2

    maze_size = 6
    maze_map = """
xxxxxx
x    x
x xx x
x  x x
xx   x
xxxxxx
"""

    def get_interaction(self, label: str, valence: int = 0) -> Interaction:
        return self.interactions.setdefault(label, PrimitiveInteraction(label, valence))

    def perform(self, intended: Interaction) -> Interaction:
        enacted = None

        if intended.label.startswith('|'):
            enacted = self.move_forward()
        elif intended.label.startswith('^'):
            enacted = self.move_left()
        elif intended.label.startswith('v'):
            enacted = self.move_right()
        elif intended.label.startswith('-'):
            enacted = self.touch_forward()
        elif intended.label.startswith('/'):
            enacted = self.touch_left()
        elif intended.label.startswith('\\'):
            enacted = self.touch_right()

        position = self._to_index(self.agent_position)

        maze = list(self.maze_map)
        maze[position] = self.agent_icons[self.agent_orientation]
        print(''.join(maze))
        sleep(.1)

        return enacted

    def _to_index(self, position):
        return position[1] * (1 + self.maze_size) + position[0] + 1

    def _empty(self, position):
        idx = self._to_index(position)
        return list(self.maze_map)[idx] == ' '

    def touch_left(self):
        x, y = self.agent_position

        if (
            (self.agent_orientation == 0 and x > 0 and self._empty((x-1, y)))
            or (self.agent_orientation == 1 and y > 0 and self._empty((x, y-1)))
            or (self.agent_orientation == 2 and x < 6 and self._empty((x+1, y)))
            or (self.agent_orientation == 3 and y < 6 and self._empty((x, y+1)))
        ):
            return self.get_interaction('/f')
        return self.get_interaction('/t')

    def touch_right(self):
        x, y = self.agent_position

        if (
            (self.agent_orientation == 0 and x > 0 and self._empty((x+1, y)))
            or (self.agent_orientation == 1 and y < 6 and self._empty((x, y+1)))
            or (self.agent_orientation == 2 and x < 6 and self._empty((x-1, y)))
            or (self.agent_orientation == 3 and y > 0 and self._empty((x, y-1)))
        ):
            return self.get_interaction('\\f')
        return self.get_interaction('\\t')

    def touch_forward(self):
        x, y = self.agent_position

        if (
            (self.agent_orientation == 0 and y > 0 and self._empty((x, y-1)))
            or (self.agent_orientation == 1 and x > 0 and self._empty((x-1, y)))
            or (self.agent_orientation == 2 and y < 6 and self._empty((x, y+1)))
            or (self.agent_orientation == 3 and x < 6 and self._empty((x+1, y)))
        ):
            return self.get_interaction('-f')
        return self.get_interaction('-t')

    def move_left(self):
        self.agent_orientation = (self.agent_orientation - 1) % 4
        return self.get_interaction('^t')

    def move_right(self):
        self.agent_orientation = (self.agent_orientation + 1) % 4
        return self.get_interaction('vt')

    def move_forward(self):
        x, y = self.agent_position

        if (
            self.agent_orientation == 0
            and y > 0
            and self._empty((x, y - 1))
        ):
            self.agent_position = (x, y - 1)
            return self.get_interaction('|t')

        if (
            self.agent_orientation == 2
            and y < 6
            and self._empty((x, y + 1))
        ):
            self.agent_position = (x, y + 1)
            return self.get_interaction('|t')

        if (
            self.agent_orientation == 1
            and x < 6
            and self._empty((x + 1, y))
        ):
            self.agent_position = (x + 1, y)
            return self.get_interaction('|t')

        if (
            self.agent_orientation == 3
            and x > 0
            and self._empty((x - 1, y))
        ):
            self.agent_position = (x - 1, y)
            return self.get_interaction('|t')

        return self.get_interaction('|f')


@attr.s
class Existence:
    env = attr.ib()

    mood = None
    memory = (None, None)
    experiments = dict()
    interactions = dict()

    def __attrs_post_init__(self):
        turn_left = self.env.get_interaction("^t", -3)
        turn_right = self.env.get_interaction("vt", -3)
        touch_left = self.env.get_interaction("/t", -1)
        touch_right = self.env.get_interaction("\\t", -1)
        touch_left_empty = self.env.get_interaction("/f", -1)
        touch_right_empty = self.env.get_interaction("\\f", -1)
        move_forward = self.env.get_interaction("|t", 5)
        bump_forward = self.env.get_interaction("|f", -10)
        touch_forward = self.env.get_interaction("-t", -1)
        touch_forward_empty = self.env.get_interaction("-f", -1)

        self.get_abstract_experiment(turn_left)
        self.get_abstract_experiment(turn_right)
        self.get_abstract_experiment(touch_left)
        self.get_abstract_experiment(touch_right)
        self.get_abstract_experiment(move_forward)
        self.get_abstract_experiment(touch_forward)


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
        #print(
        #    f"learn: {interaction.label} | {interaction.valence} | {interaction.weight}"
        #)
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
            Anticipation(e, e.intended.valence)
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

        #for a in anticipations[:5]:
        #    print(f"propose: {a.experiment.label} | {a.proclivity}")
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
                #print(f"reinforce: {i.label} | {i.valence} | {i.weight}")
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
        enacted = self.enact_composite(intended)

        print(f"intended: {intended.label} | {intended.valence}")
        print(f"enacted: {enacted.label} | {enacted.valence}")

        #if intended != enacted:
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

    for i in range(1000):
        trace = existence.step()
        print(f"{i:02d}: {trace}")
        print(15 * "-")

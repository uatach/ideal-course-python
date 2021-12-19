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
    label = attr.ib()
    experience = attr.ib(None)
    result = attr.ib(None)
    valence = attr.ib(None)
    prev_interaction = attr.ib(None)
    next_interaction = attr.ib(None)
    weight = attr.ib(0)

    def is_primitive(self) -> bool:
        return self.prev_interaction is None


@attr.s
class Anticipation:
    experience = attr.ib(order=False)
    proclivity = attr.ib(eq=False)


@attr.s
class Existence:
    mood = attr.ib(None)
    experiences = attr.ib(factory=dict)
    interactions = attr.ib(factory=dict)
    results = attr.ib(factory=dict)
    satisfaction = attr.ib(0)
    prev_experience = attr.ib(None)
    enacted_interaction = attr.ib(None)
    clock = 0

    def __attrs_post_init__(self):
        e1 = self.get_experience("e1")
        e2 = self.get_experience("e2")
        r1 = self.get_result("r1")
        r2 = self.get_result("r2")
        self.setup_interaction(e1, r1, -1)
        self.setup_interaction(e1, r2, 1)
        self.setup_interaction(e2, r1, -1)
        self.setup_interaction(e2, r2, 1)

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

    def get_composite_interaction(self, prev_interaction: Interaction, next_interaction: Interaction) -> Interaction:
        valence = prev_interaction.valence + next_interaction.valence
        interaction = self.get_interaction(prev_interaction.label + next_interaction.label)
        interaction.prev_interaction = prev_interaction
        interaction.next_interaction = next_interaction
        interaction.valence = valence
        print(f'learn: {interaction.label} | {interaction.valence}')
        return interaction

    # unused
    def swap_experience(self, experience: Experiment) -> Experiment:
        for e in self.experiences.values():
            if e != experience:
                return e

    def swap_interaction(self, interaction: typing.Optional[Interaction]) -> Interaction:
        if interaction is None:
            return list(self.interactions.values())[0]

        for i in self.interactions.values():
            if i.experience is not None and i.experience != interaction.experience:
                return i

    def setup_interaction(
        self, experience: Experiment, result: Result, valence: int = None
    ) -> Interaction:
        interaction = self.get_interaction(experience.label + result.label)
        interaction.experience = experience
        interaction.result = result
        if valence:
            interaction.valence = valence
        return interaction

    def learn_composite_interaction(self, interaction: Interaction):
        prev_interaction = self.enacted_interaction
        next_interaction = interaction
        if prev_interaction is not None:
            i = self.get_composite_interaction(prev_interaction, next_interaction)
            i.weight += 1

    # unused
    def predict_result(self, experience: Experiment) -> Result:
        for i in self.interactions.values():
            if i.experience == experience and i.valence > 0:
                return i.result
        return None

    def get_activated_interactions(self) -> typing.List[Interaction]:
        interactions = []
        if self.enacted_interaction is not None:
            for i in self.interactions.values():
                if i.prev_interaction == self.enacted_interaction:
                    interactions.append(i)
        return interactions

    def anticipate(self) -> typing.List[Anticipation]:
        anticipations = [Anticipation(e, 0) for e in self.experiences.values()]
        if self.enacted_interaction is not None:
            for i in self.get_activated_interactions():
                proclivity = i.weight * i.next_interaction.valence
                proposition = Anticipation(i.next_interaction.experience, proclivity)
                for x in anticipations:
                    if proposition.experience == x.experience:
                        x.proclivity = proposition.proclivity
                        break
                else:
                    anticipations.append(proposition)
        return anticipations

    def select_interaction(self, anticipations: typing.List[Anticipation]) -> Interaction:
        anticipations = list(reversed(sorted(anticipations)))

        if len(anticipations):
            interaction = anticipations[0].interaction
            if interaction.valence >= 0:
                return interaction
            return self.swap_interaction(interaction)
        return self.swap_interaction(None)

    def select_experience(self, anticipations: typing.List[Anticipation]) -> Experiment:
        anticipations = list(sorted(anticipations))

        for x in anticipations:
            print(f'propose: {x.experience.label} | {x.proclivity}')

        return anticipations[0].experience

    def step(self) -> str:
        anticipations = self.anticipate()
        experience = self.select_experience(anticipations)

        result = self.create_result(experience)

        interaction = self.get_interaction(experience.label + result.label)
        print(f'enacted: {interaction.label} | {interaction.valence}')

        if interaction.valence >= 0:
            self.mood = 'pleased'
        else:
            self.mood = 'pained'

        self.learn_composite_interaction(interaction)
        self.enacted_interaction = interaction

        return self.mood

    def create_result(self, experience: Experiment) -> Result:
        self.clock += 1

        if self.clock <= 8 or self.clock > 15:
            if experience == self.get_experience('e1'):
                return self.get_result('r1')
            return self.get_result('r2')

        if experience == self.get_experience('e1'):
            return self.get_result('r2')
        return self.get_result('r1')


if __name__ == "__main__":
    existence = Existence()

    for i in range(20):
        trace = existence.step()
        print(f"{i:02d}: {trace}")

import rx
import attr
import typing

from rx import operators as ops


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
    def generate_result(self, x: typing.Tuple) -> typing.Tuple:
        idx = x[2].label[-1]
        return (x[0], x[1], x[2], Result(f'r{idx}'))


@attr.s
class Agent:
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

    def generate_experiment(self, x: typing.Any) -> typing.Tuple:
        experiment = self.experience

        if self.mood == 'bored':
            experiment = self.swap(experiment)
            self.satisfaction = 0

        self.anticipated = self.predict(experiment)
        return (str(x.timestamp), x.value, experiment)

    def handle_interaction(self, x: typing.Tuple) -> typing.Tuple:
        interaction = self.get_interaction(x[2], x[3])

        if self.anticipated == x[3]:
            self.mood = 'satisfied'
            self.satisfaction += 1
        else:
            self.mood = 'frustrated'
            self.satisfaction = 0

        if self.satisfaction > 4:
            self.mood = 'bored'

        self.experience = x[2]
        return (*x, interaction.label, self.mood)


if __name__ == '__main__':
    scheduler = rx.scheduler.ThreadPoolScheduler(10)

    env = Environment()
    agent = Agent()

    _ = (
        rx.interval(.1, scheduler=scheduler)
        .pipe(
            ops.timestamp(),
            ops.take(20),
            #ops.observe_on(scheduler),
            ops.map(agent.generate_experiment),
            ops.map(env.generate_result),
            ops.map(agent.handle_interaction),
        )
        .subscribe(
            on_next=lambda x: print(f'{x[1]:02d}: {x[4]} {x[5]}'),
            #on_completed=lambda: print('done'),
            scheduler=scheduler,
        )
    )

    #input('wait\n')

import os
import random
from qubots.base_problem import BaseProblem

class AssemblyLineBalancingProblem(BaseProblem):
    """
    Assembly Line Balancing Problem (SALBP):
    
    Given a set of tasks (each with a processing time) and precedence constraints,
    assign each task to a station (numbered from 0 to nb_tasks-1) so that:
      - The total processing time at each station does not exceed the cycle time limit.
      - For every precedence relation (i -> j), the station assigned to i is not after j.
    
    The objective is to minimize the number of stations used.
    
    Instance data is read from a file (see data_format in problem_config.json) and is
    assumed to be structured as follows:
      - Some header tokens to skip.
      - The number of tasks.
      - Some tokens to skip.
      - The cycle time limit.
      - Additional tokens to skip.
      - Processing times: for each task, a pair (task number, processing time).
      - More tokens, then precedence relations in the form "pred,succ".
    """
    
    def __init__(self, instance_file=None, nb_tasks=None, max_nb_stations=None,
                 cycle_time=None, processing_time=None, successors=None):
        if instance_file is not None:
            self._load_instance_from_file(instance_file)
        else:
            if (nb_tasks is None or max_nb_stations is None or cycle_time is None or 
                processing_time is None or successors is None):
                raise ValueError("Either 'instance_file' or all instance parameters must be provided.")
            self.nb_tasks = nb_tasks
            self.max_nb_stations = max_nb_stations
            self.cycle_time = cycle_time
            self.processing_time = processing_time
            self.successors = successors

    def _load_instance_from_file(self, filename):
        # Resolve relative paths with respect to this module's directory.
        if not os.path.isabs(filename):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            filename = os.path.join(base_dir, filename)
        with open(filename, "r") as f:
            tokens = f.read().split()
        file_it = iter(tokens)
        # Skip 3 tokens (header info)
        for _ in range(3):
            next(file_it)
        # Read number of tasks.
        self.nb_tasks = int(next(file_it))
        # Maximum number of stations is set to number of tasks.
        self.max_nb_stations = self.nb_tasks
        # Skip next 2 tokens.
        for _ in range(2):
            next(file_it)
        # Read cycle time limit.
        self.cycle_time = int(next(file_it))
        # Skip next 5 tokens.
        for _ in range(5):
            next(file_it)
        # Read processing times.
        processing_time_dict = {}
        for _ in range(self.nb_tasks):
            task = int(next(file_it)) - 1  # tasks are numbered from 1 in the file
            processing_time_dict[task] = int(next(file_it))
        for _ in range(2):
            next(file_it)
        # Order processing times by task index.
        self.processing_time = [elem[1] for elem in sorted(processing_time_dict.items(), key=lambda x: x[0])]
        # Read precedence relations (successors).
        self.successors = {}
        while True:
            try:
                pair = next(file_it)
            except StopIteration:
                break
            if ',' in pair:
                pred, succ = pair.split(',')
                pred = int(pred) - 1
                succ = int(succ) - 1
                if pred in self.successors:
                    self.successors[pred].append(succ)
                else:
                    self.successors[pred] = [succ]

    def evaluate_solution(self, solution) -> float:
        """
        Evaluate a candidate solution.
        
        The candidate solution should be a list of integers (length = nb_tasks) where
        solution[i] is the station number assigned to task i (0-indexed).
        
        Constraints:
          - For each station, the total processing time of tasks assigned to it must
            not exceed the cycle time limit.
          - For each precedence relation (i -> j), require solution[i] <= solution[j].
        
        If any constraint is violated, a large penalty is returned.
        Otherwise, the objective is the number of used stations (i.e., the count of unique station numbers).
        """
        PENALTY = 1e9
        if not isinstance(solution, (list, tuple)) or len(solution) != self.nb_tasks:
            raise ValueError("Solution must be a list/tuple of length equal to the number of tasks.")
        # Check that each station number is valid.
        for s in solution:
            if not isinstance(s, int) or s < 0 or s >= self.max_nb_stations:
                return PENALTY
        
        # Check cycle time constraints for each station.
        station_times = {}
        for i, station in enumerate(solution):
            station_times.setdefault(station, 0)
            station_times[station] += self.processing_time[i]
            if station_times[station] > self.cycle_time:
                return PENALTY
        
        # Check precedence constraints: for each precedence (i -> j), require station[i] <= station[j].
        for i, succs in self.successors.items():
            for j in succs:
                if solution[i] > solution[j]:
                    return PENALTY
        
        # Feasible solution: objective = number of used stations.
        num_stations_used = len(set(solution))
        return num_stations_used

    def random_solution(self):
        """
        Generate a random candidate solution.
        
        Each task is randomly assigned a station number between 0 and (max_nb_stations - 1).
        Note: The generated solution may be infeasible.
        """
        return [random.randint(0, self.max_nb_stations - 1) for _ in range(self.nb_tasks)]

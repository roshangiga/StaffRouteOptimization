from ortools.sat.python import cp_model
import pandas as pd


class StaffScheduler:
    def __init__(self, num_staff, num_days=30):
        self.num_staff = num_staff
        self.num_days = num_days
        self.shifts = {
            'A': (8, 0, 15, 30),  # 08:00 - 15:30
            'B': (13, 0, 21, 0),  # 13:00 - 21:00
            'C': (14, 30, 22, 0),  # 14:30 - 22:00
            'D': (16, 0, 23, 30),  # 16:00 - 23:30
            'OFF': (-1, -1, -1, -1)  # Off day
        }
        self.desired_staff_per_shift = {
            'A': 10,
            'B': 8,
            'C': 9,
            'D': 5
        }
        self.model = cp_model.CpModel()
        self.vars = {}

    def create_variables(self):
        for s in range(self.num_staff):
            for d in range(self.num_days):
                for shift in self.shifts:
                    self.vars[(s, d, shift)] = self.model.NewBoolVar(f'staff_{s}_day_{d}_shift_{shift}')

    def add_constraints(self):
        # One shift per day per staff
        for s in range(self.num_staff):
            for d in range(self.num_days):
                self.model.Add(sum(self.vars[(s, d, shift)] for shift in self.shifts) == 1)

        # a) 1 day OFF over period of 7 days
        for s in range(self.num_staff):
            for week in range(self.num_days // 7):
                week_days = range(week * 7, (week + 1) * 7)
                self.model.Add(sum(self.vars[(s, d, 'OFF')] for d in week_days) == 1)

        # b) Not more than 3 consecutive nights for shift staff
        night_shifts = ['C', 'D']
        for s in range(self.num_staff):
            for d in range(self.num_days - 3):
                self.model.Add(sum(self.vars[(s, d + i, shift)] for i in range(4) for shift in night_shifts) <= 3)

        # c) At least 11hrs rest between shifts
        for s in range(self.num_staff):
            for d in range(self.num_days - 1):
                for shift1 in self.shifts:
                    for shift2 in self.shifts:
                        if shift1 != 'OFF' and shift2 != 'OFF':
                            end_time1 = self.shifts[shift1][2] * 60 + self.shifts[shift1][3]
                            start_time2 = self.shifts[shift2][0] * 60 + self.shifts[shift2][1]
                            if (start_time2 - end_time1 + 24 * 60) % (24 * 60) < 11 * 60:
                                self.model.Add(self.vars[(s, d, shift1)] + self.vars[(s, d + 1, shift2)] <= 1)

        # d) At least 24hrs during rest day (implicitly satisfied)

        # e) Perform a minimum of 45 hours per week
        for s in range(self.num_staff):
            for week in range(self.num_days // 7):
                week_days = range(week * 7, (week + 1) * 7)
                total_minutes = sum(self.vars[(s, d, shift)] * ((self.shifts[shift][2] * 60 + self.shifts[shift][3]) - (
                            self.shifts[shift][0] * 60 + self.shifts[shift][1]) - 60)
                                    for d in week_days for shift in self.shifts if shift != 'OFF')
                self.model.Add(total_minutes >= 40 * 60)
                self.model.Add(total_minutes <= 50 * 60)

        # f) Rest day preference for Sunday
        for s in range(self.num_staff):
            self.model.Maximize(sum(self.vars[(s, 6 + week * 7, 'OFF')] for week in range(self.num_days // 7)))

        # Ensure each shift is covered each day
        for d in range(self.num_days):
            for shift in self.shifts:
                if shift != 'OFF':
                    self.model.Add(sum(self.vars[(s, d, shift)] for s in range(self.num_staff)) >= 1)

        # Soft constraints for balancing the number of staff for each shift
        for shift, desired_count in self.desired_staff_per_shift.items():
            for d in range(self.num_days):
                staff_count = sum(self.vars[(s, d, shift)] for s in range(self.num_staff))
                deviation = self.model.NewIntVar(-self.num_staff, self.num_staff, f'deviation_{shift}_{d}')
                abs_deviation = self.model.NewIntVar(0, self.num_staff, f'abs_deviation_{shift}_{d}')
                self.model.Add(deviation == staff_count - desired_count)
                self.model.AddAbsEquality(abs_deviation, deviation)
                self.model.Minimize(abs_deviation)

    def solve(self):
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 120.0
        status = solver.Solve(self.model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            schedule = {}
            for s in range(self.num_staff):
                schedule[s] = {}
                for d in range(self.num_days):
                    for shift in self.shifts:
                        if solver.Value(self.vars[(s, d, shift)]) == 1:
                            schedule[s][d] = shift
            return schedule, solver
        else:
            return None, None

    def format_time(self, hour, minute):
        return f"{hour:02d}:{minute:02d}"

    def print_schedule(self, schedule, solver):
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        col_width = 15

        # Prepare data for the DataFrame
        data = []
        for s in range(self.num_staff):
            staff_row = []
            for d in range(self.num_days):
                shift = schedule[s][d]
                if shift == 'OFF':
                    staff_row.append('OFF')
                else:
                    start_hour, start_minute, end_hour, end_minute = self.shifts[shift]
                    start_time = self.format_time(start_hour, start_minute)
                    end_time = self.format_time(end_hour, end_minute)
                    time_range = f"{start_time}-{end_time}"
                    staff_row.append(time_range)
            data.append(staff_row)

        # Create DataFrame
        df = pd.DataFrame(data, columns=[f"Day {i + 1}" for i in range(self.num_days)],
                          index=[f"Staff {i}" for i in range(self.num_staff)])

        # Set display options to avoid truncation
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.expand_frame_repr', False)

        # Display DataFrame
        display(df)

        self.print_summary(schedule, solver)

    def print_summary(self, schedule, solver):
        # Print summary
        total_hours_worked = {s: 0 for s in range(self.num_staff)}
        for s in range(self.num_staff):
            for d in range(self.num_days):
                shift = schedule[s][d]
                if shift != 'OFF':
                    start_hour, start_minute, end_hour, end_minute = self.shifts[shift]
                    total_hours_worked[s] += ((end_hour * 60 + end_minute) - (start_hour * 60 + start_minute) - 60) / 60
        print("\nSummary:")
        for s in range(self.num_staff):
            print(f"Staff {s} total hours worked: {total_hours_worked[s]} hours")
        for d in range(self.num_days):
            print(f"\nDay {d + 1}:")
            for shift in self.shifts:
                if shift != 'OFF':
                    num_staff_scheduled = sum(solver.Value(self.vars[(s, d, shift)]) for s in range(self.num_staff))
                    print(f"  Shift {shift}: {num_staff_scheduled} staff")


def main():
    num_staff = 48  # Keeping the increased number of staff
    scheduler = StaffScheduler(num_staff)
    scheduler.create_variables()
    scheduler.add_constraints()
    schedule, solver = scheduler.solve()

    if schedule:
        print("Feasible schedule found:")
        scheduler.print_schedule(schedule, solver)
    else:
        print("No feasible schedule found.")


if __name__ == "__main__":
    main()

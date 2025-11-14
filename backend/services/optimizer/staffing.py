"""
Staffing Optimization using PuLP

Solves workforce scheduling problems:
- Shift scheduling (minimize cost, meet coverage requirements)
- Employee assignment optimization
- Break scheduling
- Overtime minimization
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, time, timedelta

import pulp

logger = logging.getLogger(__name__)


class StaffingOptimizer:
    """
    Staffing optimization using PuLP (linear programming).
    
    Methods:
    - optimize_shift_schedule(): Generate optimal shift assignments
    - optimize_employee_assignment(): Assign employees to tasks
    - calculate_labor_cost(): Calculate total labor cost
    """
    
    def __init__(self):
        """Initialize optimizer."""
        self.logger = logging.getLogger(__name__)
    
    def optimize_shift_schedule(
        self,
        employees: list[dict[str, Any]],
        shifts: list[dict[str, Any]],
        min_coverage: dict[str, int],
        max_hours_per_week: int = 40,
        planning_horizon_days: int = 7
    ) -> dict[str, Any]:
        """
        Optimize shift scheduling to minimize labor cost.
        
        Objective: Minimize total labor cost
        Constraints:
        - Meet minimum coverage requirements per shift
        - Respect employee availability
        - Stay within max hours per employee
        - Respect employee skill requirements
        
        Args:
            employees: List of employee dicts with keys:
                - id: Employee ID
                - name: Employee name
                - hourly_rate: Hourly wage ($)
                - max_hours: Max hours this employee can work
                - skills: List of skills (e.g., ["cashier", "cook"])
                - availability: Dict of day -> list of available shift IDs
            shifts: List of shift dicts with keys:
                - id: Shift ID
                - name: Shift name (e.g., "Mon-Morning")
                - day: Day of week (0=Monday, 6=Sunday)
                - start_time: Start time (HH:MM)
                - end_time: End time (HH:MM)
                - duration_hours: Shift duration in hours
                - required_skills: List of required skills
            min_coverage: Dict of shift_id -> min number of employees needed
            max_hours_per_week: Max hours per employee per week
            planning_horizon_days: Number of days to schedule
        
        Returns:
            Optimization result with shift assignments and costs
        """
        if not employees or not shifts:
            raise ValueError("Employees and shifts lists cannot be empty")
        
        self.logger.info(
            f"Optimizing schedule for {len(employees)} employees, "
            f"{len(shifts)} shifts, {planning_horizon_days} days"
        )
        
        # Create optimization problem
        prob = pulp.LpProblem("Shift_Scheduling", pulp.LpMinimize)
        
        # Decision variables: x[e][s] = 1 if employee e works shift s
        x = {}
        for emp in employees:
            for shift in shifts:
                var_name = f"x_{emp['id']}_{shift['id']}"
                x[(emp['id'], shift['id'])] = pulp.LpVariable(
                    var_name,
                    cat='Binary'
                )
        
        # Objective: Minimize total labor cost
        # Cost = Σ (employee_rate * shift_duration * x[e][s])
        prob += pulp.lpSum([
            emp['hourly_rate'] * shift['duration_hours'] * x[(emp['id'], shift['id'])]
            for emp in employees
            for shift in shifts
        ]), "Total_Labor_Cost"
        
        # Constraint 1: Meet minimum coverage for each shift
        for shift in shifts:
            min_required = min_coverage.get(shift['id'], 1)
            prob += (
                pulp.lpSum([
                    x[(emp['id'], shift['id'])]
                    for emp in employees
                ]) >= min_required,
                f"Min_Coverage_Shift_{shift['id']}"
            )
        
        # Constraint 2: Respect employee max hours per week
        for emp in employees:
            emp_max_hours = min(emp.get('max_hours', max_hours_per_week), max_hours_per_week)
            prob += (
                pulp.lpSum([
                    shift['duration_hours'] * x[(emp['id'], shift['id'])]
                    for shift in shifts
                ]) <= emp_max_hours,
                f"Max_Hours_Employee_{emp['id']}"
            )
        
        # Constraint 3: Employee availability
        # Only assign employee to shifts they're available for
        for emp in employees:
            availability = emp.get('availability', {})
            for shift in shifts:
                day_str = str(shift['day'])
                available_shifts = availability.get(day_str, [])
                
                # If shift not in available shifts, set x = 0
                if shift['id'] not in available_shifts and availability:
                    prob += (
                        x[(emp['id'], shift['id'])] == 0,
                        f"Availability_{emp['id']}_Shift_{shift['id']}"
                    )
        
        # Constraint 4: Skill requirements
        # Only assign employees who have required skills
        for shift in shifts:
            required_skills = shift.get('required_skills', [])
            if required_skills:
                for emp in employees:
                    emp_skills = set(emp.get('skills', []))
                    required_skills_set = set(required_skills)
                    
                    # If employee doesn't have all required skills, set x = 0
                    if not required_skills_set.issubset(emp_skills):
                        prob += (
                            x[(emp['id'], shift['id'])] == 0,
                            f"Skills_{emp['id']}_Shift_{shift['id']}"
                        )
        
        # Constraint 5: No overlapping shifts for same employee
        # Group shifts by day and check for time overlaps
        shifts_by_day = {}
        for shift in shifts:
            day = shift['day']
            if day not in shifts_by_day:
                shifts_by_day[day] = []
            shifts_by_day[day].append(shift)
        
        for emp in employees:
            for day, day_shifts in shifts_by_day.items():
                # Check each pair of shifts on same day
                for i, shift1 in enumerate(day_shifts):
                    for shift2 in day_shifts[i+1:]:
                        if self._shifts_overlap(shift1, shift2):
                            # Can't work both overlapping shifts
                            prob += (
                                x[(emp['id'], shift1['id'])] + x[(emp['id'], shift2['id'])] <= 1,
                                f"No_Overlap_{emp['id']}_Day_{day}_Shifts_{shift1['id']}_{shift2['id']}"
                            )
        
        # Solve
        solver = pulp.PULP_CBC_CMD(msg=0)  # Suppress solver output
        prob.solve(solver)
        
        status = pulp.LpStatus[prob.status]
        
        if status == "Optimal":
            self.logger.info("Optimal schedule found")
            
            # Extract assignments
            assignments = []
            total_cost = 0
            employee_hours = {emp['id']: 0 for emp in employees}
            shift_coverage = {shift['id']: 0 for shift in shifts}
            
            for emp in employees:
                for shift in shifts:
                    if x[(emp['id'], shift['id'])].varValue == 1:
                        cost = emp['hourly_rate'] * shift['duration_hours']
                        total_cost += cost
                        employee_hours[emp['id']] += shift['duration_hours']
                        shift_coverage[shift['id']] += 1
                        
                        assignments.append({
                            "employee_id": emp['id'],
                            "employee_name": emp['name'],
                            "shift_id": shift['id'],
                            "shift_name": shift['name'],
                            "day": shift['day'],
                            "start_time": shift['start_time'],
                            "end_time": shift['end_time'],
                            "duration_hours": shift['duration_hours'],
                            "hourly_rate": emp['hourly_rate'],
                            "shift_cost": round(cost, 2)
                        })
            
            # Calculate coverage statistics
            coverage_met = all(
                shift_coverage[shift['id']] >= min_coverage.get(shift['id'], 1)
                for shift in shifts
            )
            
            # Calculate employee utilization
            employee_stats = []
            for emp in employees:
                hours = employee_hours[emp['id']]
                max_hours = min(emp.get('max_hours', max_hours_per_week), max_hours_per_week)
                utilization = hours / max_hours if max_hours > 0 else 0
                
                employee_stats.append({
                    "employee_id": emp['id'],
                    "employee_name": emp['name'],
                    "hours_scheduled": round(hours, 1),
                    "max_hours": max_hours,
                    "utilization": round(utilization, 2),
                    "total_pay": round(hours * emp['hourly_rate'], 2)
                })
            
            return {
                "status": "optimal",
                "assignments": assignments,
                "total_cost": round(total_cost, 2),
                "total_hours_scheduled": round(sum(employee_hours.values()), 1),
                "coverage_met": coverage_met,
                "shift_coverage": shift_coverage,
                "employee_stats": employee_stats,
                "avg_utilization": round(
                    sum(s['utilization'] for s in employee_stats) / len(employee_stats) if employee_stats else 0,
                    2
                ),
                "solver_time_seconds": prob.solutionTime
            }
        
        elif status == "Infeasible":
            self.logger.error("No feasible schedule exists")
            return {
                "status": "infeasible",
                "message": "Cannot create schedule with given constraints. Try relaxing coverage requirements or employee availability."
            }
        
        else:
            self.logger.warning(f"Solver status: {status}")
            return {
                "status": status.lower(),
                "message": f"Solver returned status: {status}"
            }
    
    def _shifts_overlap(self, shift1: dict[str, Any], shift2: dict[str, Any]) -> bool:
        """
        Check if two shifts overlap in time.
        
        Args:
            shift1: First shift dict with start_time and end_time
            shift2: Second shift dict with start_time and end_time
        
        Returns:
            True if shifts overlap, False otherwise
        """
        # Parse time strings (HH:MM format)
        def parse_time(time_str: str) -> time:
            parts = time_str.split(':')
            return time(int(parts[0]), int(parts[1]))
        
        start1 = parse_time(shift1['start_time'])
        end1 = parse_time(shift2['end_time'])
        start2 = parse_time(shift2['start_time'])
        end2 = parse_time(shift2['end_time'])
        
        # Shifts overlap if one starts before the other ends
        return start1 < end2 and start2 < end1
    
    def optimize_employee_assignment(
        self,
        employees: list[dict[str, Any]],
        tasks: list[dict[str, Any]],
        max_tasks_per_employee: int = 10
    ) -> dict[str, Any]:
        """
        Assign employees to tasks to maximize total value.
        
        Useful for project assignment, task allocation, etc.
        
        Args:
            employees: List of employee dicts with keys:
                - id: Employee ID
                - name: Employee name
                - skills: List of skills
                - capacity: Max number of tasks
            tasks: List of task dicts with keys:
                - id: Task ID
                - name: Task name
                - required_skills: List of required skills
                - value: Value/priority of task (higher = more important)
                - effort: Effort required (in employee capacity units)
            max_tasks_per_employee: Max tasks per employee
        
        Returns:
            Optimization result with task assignments
        """
        if not employees or not tasks:
            raise ValueError("Employees and tasks lists cannot be empty")
        
        self.logger.info(
            f"Optimizing task assignment for {len(employees)} employees, {len(tasks)} tasks"
        )
        
        # Create optimization problem
        prob = pulp.LpProblem("Task_Assignment", pulp.LpMaximize)
        
        # Decision variables: y[e][t] = 1 if employee e assigned to task t
        y = {}
        for emp in employees:
            for task in tasks:
                var_name = f"y_{emp['id']}_{task['id']}"
                y[(emp['id'], task['id'])] = pulp.LpVariable(
                    var_name,
                    cat='Binary'
                )
        
        # Objective: Maximize total value of completed tasks
        prob += pulp.lpSum([
            task['value'] * y[(emp['id'], task['id'])]
            for emp in employees
            for task in tasks
        ]), "Total_Value"
        
        # Constraint 1: Each task assigned to at most one employee
        for task in tasks:
            prob += (
                pulp.lpSum([
                    y[(emp['id'], task['id'])]
                    for emp in employees
                ]) <= 1,
                f"Task_{task['id']}_Assignment"
            )
        
        # Constraint 2: Respect employee capacity
        for emp in employees:
            emp_capacity = emp.get('capacity', max_tasks_per_employee)
            prob += (
                pulp.lpSum([
                    task.get('effort', 1) * y[(emp['id'], task['id'])]
                    for task in tasks
                ]) <= emp_capacity,
                f"Employee_{emp['id']}_Capacity"
            )
        
        # Constraint 3: Skill requirements
        for task in tasks:
            required_skills = set(task.get('required_skills', []))
            if required_skills:
                for emp in employees:
                    emp_skills = set(emp.get('skills', []))
                    
                    # If employee doesn't have required skills, set y = 0
                    if not required_skills.issubset(emp_skills):
                        prob += (
                            y[(emp['id'], task['id'])] == 0,
                            f"Skills_{emp['id']}_Task_{task['id']}"
                        )
        
        # Solve
        solver = pulp.PULP_CBC_CMD(msg=0)
        prob.solve(solver)
        
        status = pulp.LpStatus[prob.status]
        
        if status == "Optimal":
            self.logger.info("Optimal assignment found")
            
            assignments = []
            total_value = 0
            unassigned_tasks = []
            employee_workload = {emp['id']: 0 for emp in employees}
            
            for task in tasks:
                assigned = False
                for emp in employees:
                    if y[(emp['id'], task['id'])].varValue == 1:
                        total_value += task['value']
                        employee_workload[emp['id']] += task.get('effort', 1)
                        assigned = True
                        
                        assignments.append({
                            "employee_id": emp['id'],
                            "employee_name": emp['name'],
                            "task_id": task['id'],
                            "task_name": task['name'],
                            "value": task['value'],
                            "effort": task.get('effort', 1)
                        })
                        break
                
                if not assigned:
                    unassigned_tasks.append({
                        "task_id": task['id'],
                        "task_name": task['name'],
                        "value": task['value'],
                        "required_skills": task.get('required_skills', [])
                    })
            
            # Employee workload stats
            employee_stats = []
            for emp in employees:
                workload = employee_workload[emp['id']]
                capacity = emp.get('capacity', max_tasks_per_employee)
                utilization = workload / capacity if capacity > 0 else 0
                
                employee_stats.append({
                    "employee_id": emp['id'],
                    "employee_name": emp['name'],
                    "workload": workload,
                    "capacity": capacity,
                    "utilization": round(utilization, 2),
                    "num_tasks": sum(1 for a in assignments if a['employee_id'] == emp['id'])
                })
            
            return {
                "status": "optimal",
                "assignments": assignments,
                "total_value": round(total_value, 2),
                "tasks_assigned": len(assignments),
                "tasks_unassigned": len(unassigned_tasks),
                "unassigned_tasks": unassigned_tasks,
                "employee_stats": employee_stats,
                "avg_utilization": round(
                    sum(s['utilization'] for s in employee_stats) / len(employee_stats) if employee_stats else 0,
                    2
                )
            }
        
        else:
            return {
                "status": status.lower(),
                "message": f"Solver returned status: {status}"
            }
    
    def calculate_labor_cost(
        self,
        assignments: list[dict[str, Any]],
        overtime_threshold_hours: float = 40,
        overtime_multiplier: float = 1.5
    ) -> dict[str, Any]:
        """
        Calculate total labor cost including overtime.
        
        Args:
            assignments: List of shift assignments
            overtime_threshold_hours: Hours per week before overtime
            overtime_multiplier: Overtime pay multiplier (e.g., 1.5x)
        
        Returns:
            Labor cost breakdown
        """
        # Group by employee
        employee_hours = {}
        employee_rates = {}
        
        for assignment in assignments:
            emp_id = assignment['employee_id']
            hours = assignment.get('duration_hours', 0)
            rate = assignment.get('hourly_rate', 0)
            
            if emp_id not in employee_hours:
                employee_hours[emp_id] = 0
                employee_rates[emp_id] = rate
            
            employee_hours[emp_id] += hours
        
        # Calculate costs
        regular_cost = 0
        overtime_cost = 0
        
        for emp_id, total_hours in employee_hours.items():
            rate = employee_rates[emp_id]
            
            if total_hours <= overtime_threshold_hours:
                # All regular hours
                regular_cost += total_hours * rate
            else:
                # Regular + overtime
                regular_hours = overtime_threshold_hours
                overtime_hours = total_hours - overtime_threshold_hours
                
                regular_cost += regular_hours * rate
                overtime_cost += overtime_hours * rate * overtime_multiplier
        
        total_cost = regular_cost + overtime_cost
        
        return {
            "total_cost": round(total_cost, 2),
            "regular_cost": round(regular_cost, 2),
            "overtime_cost": round(overtime_cost, 2),
            "overtime_percentage": round(overtime_cost / total_cost if total_cost > 0 else 0, 2),
            "num_employees": len(employee_hours),
            "total_hours": round(sum(employee_hours.values()), 1)
        }


# Global instance
_optimizer: StaffingOptimizer | None = None


def get_staffing_optimizer() -> StaffingOptimizer:
    """Get or create global staffing optimizer."""
    global _optimizer
    if _optimizer is None:
        _optimizer = StaffingOptimizer()
    return _optimizer

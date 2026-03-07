from crewai import Task
from agents import business_analyst, design_agent,developer_agent,tester_agent

# Business analyst task - ultra fast
business_analyst_task = Task(
    description="Create 3-5 user stories: 'As a [role], I want [action], so [benefit]'. Brief acceptance criteria.",
    agent=business_analyst,
    expected_output="User stories list",
)

# Design agent task - ultra fast
design_task = Task(
    description="Brief architecture: components, database, tech stack for {topic}.",
    inputs=["topic"],
    agent=design_agent, 
    expected_output="Architecture summary",
)

# Developer task - ultra fast
developer_task = Task(
    description="Generate clean modular code for {topic}. Keep it simple.",
    inputs=["topic"],
    agent=developer_agent,
    expected_output="Code",
)

# Tester task - ultra fast
tester_task = Task(
    description="Create key test cases for {topic}. Focus on main scenarios.",
    inputs=["topic"],
    agent=tester_agent,
    expected_output="Test cases",
)


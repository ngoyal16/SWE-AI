from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ...common.llm import get_llm
from ...callbacks import SessionCallbackHandler
from ..state import AgentState, log_update

def plan_critic_node(state: AgentState) -> AgentState:
    print(f"[{state['session_id']}] PLAN CRITIC: Reviewing plan...")
    llm = get_llm()
    callbacks = [SessionCallbackHandler(state["session_id"])]

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Technical Plan Critic. Review the proposed plan for safety, completeness, and feasibility. If the plan is good, respond with 'APPROVED'. If not, provide specific, constructive feedback on what steps are missing or dangerous."),
        ("human", "Goal: {goal}\nProposed Plan:\n{plan}\n\nReview the plan.")
    ])

    chain = prompt | llm | StrOutputParser()
    feedback = chain.invoke({"goal": state["goal"], "plan": state["plan"]}, config={"callbacks": callbacks})

    if "APPROVED" in feedback:
        if state.get("mode") == "review":
            state["status"] = "WAITING_FOR_USER"
            state["next_status"] = "BRANCH_NAMING"
            log_update(state, "Plan Critic Approved. Waiting for user approval before generating branch.")
        else:
            state["status"] = "BRANCH_NAMING"
        state["plan_critic_feedback"] = None
        log_update(state, "Plan Critic Approved.")
    else:
        state["status"] = "PLANNING"
        state["plan_critic_feedback"] = feedback
        log_update(state, f"Plan Critic Feedback: {feedback}")

    return state

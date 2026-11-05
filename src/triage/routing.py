"""Where a triaged ticket goes. The n8n workflow's "Choose route" step uses the same rules."""


def route(category, urgency, safety_terms=()):
    # Safety issues and anything urgent go to a person straight away.
    # safety_terms come from the keyword safety net and override the model's answer.
    if category == "safety" or urgency == "high" or safety_terms:
        return "escalate"
    if category == "feedback":
        return "product_backlog"
    return "support_queue"

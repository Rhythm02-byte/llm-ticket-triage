"""Where a triaged ticket goes. The n8n workflow's "Choose route" step uses the same rules."""


def route(category, urgency):
    # Safety issues and anything urgent go to a person straight away
    if category == "safety" or urgency == "high":
        return "escalate"
    if category == "feedback":
        return "product_backlog"
    return "support_queue"

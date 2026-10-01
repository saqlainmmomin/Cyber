"""Per-framework test criteria (D-P6-D).

Draft modules here are review inputs only. Nothing in `app/` may import a
draft module: criteria reach a `Control` only via the P6-2b converter,
after Saqlain signs off the review sheet in `tasks/criteria-review/`.
"""


def attach_criteria(domains, criteria):
    """Attach signed criteria (requirement id -> criteria) to a definition's controls in place."""
    from dataclasses import replace

    for domain in domains.values():
        for section in domain.sections.values():
            section.controls[:] = [
                replace(control, test_criteria=criteria.get(control.id, ()))
                for control in section.controls
            ]

from typing import Set


async def collect_subtree_ids(repo, department_id: int) -> Set[int]:
    ids: Set[int] = {department_id}
    children = await repo.get_direct_children(department_id)
    for child in children:
        child_ids = await collect_subtree_ids(repo, child.id)
        ids.update(child_ids)
    return ids

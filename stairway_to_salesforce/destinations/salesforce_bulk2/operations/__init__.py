from .delete import exec_delete
from .insert import exec_insert
from .replace import exec_replace
from .upsert import exec_upsert

__all__ = ["exec_insert", "exec_upsert", "exec_delete", "exec_replace"]

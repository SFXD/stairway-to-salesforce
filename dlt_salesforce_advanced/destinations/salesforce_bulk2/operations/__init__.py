from .insert import exec_insert
from .upsert import exec_upsert
from .delete import exec_delete
from .replace import exec_replace

__all__ = ["exec_insert", "exec_upsert", "exec_delete", "exec_replace"]
from app.core.constants import Collections
from app.database.connection import get_database
from app.repositories.base_repository import BaseRepository, to_object_id


class UserRepository(BaseRepository):
    sortable_fields = {"name", "email", "role", "created_at", "updated_at", "last_login"}
    default_sort_field = "name"
    searchable_fields = ["name", "email", "phone"]
    entity_name = "User"

    def __init__(self):
        super().__init__(get_database()[Collections.USERS])

    async def find_by_email(self, email: str) -> dict | None:
        return await self.find_one({"email": email.strip().lower()})

    async def add_session(self, user_id: str, session: dict, max_sessions: int) -> None:
        oid = to_object_id(user_id, self.entity_name)
        # Push the new session, then trim to the most recent `max_sessions`
        # entries so a user can't accumulate unlimited stale sessions.
        await self.collection.update_one({"_id": oid}, {"$push": {"sessions": session}})
        doc = await self.collection.find_one({"_id": oid}, {"sessions": 1})
        sessions = doc.get("sessions", []) if doc else []
        if len(sessions) > max_sessions:
            trimmed = sessions[-max_sessions:]
            await self.collection.update_one({"_id": oid}, {"$set": {"sessions": trimmed}})

    async def remove_session(self, user_id: str, jti: str) -> None:
        oid = to_object_id(user_id, self.entity_name)
        await self.collection.update_one({"_id": oid}, {"$pull": {"sessions": {"jti": jti}}})

    async def replace_session(self, user_id: str, old_jti: str, new_session: dict, max_sessions: int) -> None:
        """Refresh-token rotation: atomically drop the old session entry
        and add the new one."""
        oid = to_object_id(user_id, self.entity_name)
        await self.collection.update_one({"_id": oid}, {"$pull": {"sessions": {"jti": old_jti}}})
        await self.add_session(user_id, new_session, max_sessions)

    async def has_session(self, user_id: str, jti: str) -> bool:
        oid = to_object_id(user_id, self.entity_name)
        return await self.collection.count_documents({"_id": oid, "sessions.jti": jti}, limit=1) > 0

    async def clear_all_sessions(self, user_id: str) -> None:
        oid = to_object_id(user_id, self.entity_name)
        await self.collection.update_one({"_id": oid}, {"$set": {"sessions": []}})

    async def set_last_login(self, user_id: str, when) -> None:
        oid = to_object_id(user_id, self.entity_name)
        await self.collection.update_one({"_id": oid}, {"$set": {"last_login": when}})

    async def set_password_hash(self, user_id: str, password_hash: str) -> None:
        oid = to_object_id(user_id, self.entity_name)
        await self.collection.update_one({"_id": oid}, {"$set": {"password_hash": password_hash}})

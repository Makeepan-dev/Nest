"""GraphQL node for Mentee model."""

import strawberry

from apps.mentorship.api.internal.nodes.enum import ExperienceLevelEnum


@strawberry.type
class MenteeNode:
    """A GraphQL node representing a mentorship mentee."""

    id: str = strawberry.field(name="id", description="The unique identifier of the mentee.")   
    login: str = strawberry.field(name="login", description="The GitHub login of the mentee.")  
    name: str = strawberry.field(name="name", description="The full name of the mentee.")
    avatar_url: str = strawberry.field(name="avatarUrl", description="The GitHub avatar URL of the mentee.")
    bio: str | None = strawberry.field(default= None, name="bio", description="The biography of the mentee.")   
    experience_level: ExperienceLevelEnum = strawberry.field(name="experienceLevel", description="The experience level of the mentee.")
    domains: list[str] | None = strawberry.field(default = None, name="domains", description="The domains of interest for the mentee.")
    tags: list[str] | None = strawberry.field(default = None, name="tags", description="The tags associated with the mentee.")

    @strawberry.field(name="avatarUrl")
    def resolve_avatar_url(self) -> str:
        """Get the GitHub avatar URL of the mentee."""
        return self.avatar_url

    @strawberry.field(name="experienceLevel")
    def resolve_experience_level(self) -> str:
        """Get the experience level of the mentee."""
        return self.experience_level or "beginner"

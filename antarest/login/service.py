from typing import Optional, List

import werkzeug as werkzeug
from werkzeug.exceptions import BadRequest

from antarest.common.custom_types import JSON
from antarest.common.interfaces.eventbus import IEventBus
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.login.exceptions import UserAlreadyExistError
from antarest.login.ldap import LdapService
from antarest.login.model import (
    User,
    Group,
    Role,
    BotCreateDTO,
    Bot,
    Identity,
    UserCreateDTO,
    Password,
    IdentityDTO,
    RoleDTO,
    RoleCreationDTO,
)
from antarest.login.repository import (
    UserRepository,
    GroupRepository,
    RoleRepository,
    BotRepository,
)


class GroupNotFoundError(werkzeug.exceptions.NotFound):
    pass


class UserNotFoundError(werkzeug.exceptions.NotFound):
    pass


class LoginService:
    """
    Facade module service to handle request to manage user, group and role
    """

    def __init__(
        self,
        user_repo: UserRepository,
        bot_repo: BotRepository,
        group_repo: GroupRepository,
        role_repo: RoleRepository,
        ldap: LdapService,
        event_bus: IEventBus,
    ):
        self.users = user_repo
        self.bots = bot_repo
        self.groups = group_repo
        self.roles = role_repo
        self.ldap = ldap
        self.event_bus = event_bus

    def save_group(self, group: Group, params: RequestParameters) -> Group:
        """
        Create / Update group.
        Permission: SADMIN, GADMIN (own group)
        Args:
            group: group to stored
            params: request parameters

        Returns: group

        """
        if self.groups.get_by_name(group.name):
            raise BadRequest("Group name already exists")

        if params.user and any(
            (params.user.is_site_admin(), params.user.is_group_admin(group))
        ):
            return self.groups.save(group)
        else:
            raise UserHasNotPermissionError()

    def create_user(
        self, create: UserCreateDTO, param: RequestParameters
    ) -> Identity:
        """
        Create new user.
        Permission: SADMIN
        Args:
            create: user to create
            param: request parameters

        Returns: user stored

        """
        if param.user and param.user.is_site_admin():
            if self.users.get_by_name(create.name):
                raise UserAlreadyExistError()
            return self.users.save(
                User(name=create.name, password=Password(create.password))
            )
        else:
            raise UserHasNotPermissionError()

    def save_user(self, user: User, params: RequestParameters) -> User:
        """
        Update user data
        Permission: SADMIN, USER (own user)
        Args:
            user: new user
            params: requests parameters

        Returns: new user

        """
        if params.user and any(
            (params.user.is_site_admin(), params.user.is_himself(user))
        ):
            return self.users.save(user)
        else:
            raise UserHasNotPermissionError()

    def save_bot(self, bot: BotCreateDTO, params: RequestParameters) -> Bot:
        """
        Create bot
        Permission: User (own user)
        Args:
            bot: bot to create
            params: request parameters

        Returns: bot created

        """
        if params.user:
            role = self.roles.get(params.user.id, bot.group)
            if role and role.type.is_higher_or_equals(bot.role):
                b = self.bots.save(
                    Bot(
                        name=bot.name,
                        is_author=bot.is_author,
                        owner=params.user.id,
                    )
                )
                self.roles.save(
                    Role(group=Group(id=bot.group), type=bot.role, identity=b)
                )
                return b
            else:
                raise UserHasNotPermissionError()
        else:
            raise UserHasNotPermissionError()

    def save_role(
        self, role: RoleCreationDTO, params: RequestParameters
    ) -> Role:
        """
        Create / Update role
        Permission: SADMIN, GADMIN (own group)
        Args:
            role: new role
            params: request parameters

        Returns: role stored

        """
        role_obj = Role(
            type=role.type,
            group=self.groups.get(role.group_id),
            identity=self.users.get(role.identity_id),
        )
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(role_obj.group),
            )
        ):
            return self.roles.save(role_obj)
        else:
            raise UserHasNotPermissionError()

    def get_group(self, id: str, params: RequestParameters) -> Optional[Group]:
        """
        Get group.
        Permission: SADMIN, GADMIN (own group)

        Args:
            id: group id
            params: request parameters

        Returns: group asked

        """
        group = self.groups.get(id)
        if (
            group
            and params.user
            and any(
                (
                    params.user.is_site_admin(),
                    params.user.is_group_admin(group),
                )
            )
        ):
            return group
        else:
            raise GroupNotFoundError()

    def get_user(self, id: int, params: RequestParameters) -> Optional[User]:
        """
        Get user
        Permission: SADMIN, GADMIN (own group), USER (own user)

        Args:
            id: user id
            params: request parameters

        Returns: user

        """
        user = self.ldap.get(id) or self.users.get(id)
        if not user:
            raise UserNotFoundError()

        groups = [r.group for r in self.roles.get_all_by_user(user.id)]

        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(groups),
                params.user.is_himself(user),
            )
        ):
            return user
        else:
            raise UserNotFoundError()

    def get_user_info(
        self, id: int, params: RequestParameters
    ) -> Optional[IdentityDTO]:
        """
        Get user informations
        Permission: SADMIN, GADMIN (own group), USER (own user)

        Args:
            id: user id
            params: request parameters

        Returns: user informations and roles

        """
        user = self.get_user(id, params)
        if user:
            return IdentityDTO(
                id=user.id,
                name=user.name,
                roles=[
                    RoleDTO(
                        group_id=role.group_id,
                        group_name=role.group.name,
                        identity_id=id,
                        type=role.type.value,
                    )
                    for role in self.roles.get_all_by_user(user.id)
                ],
            )
        else:
            raise UserNotFoundError()

    def get_bot(self, id: int, params: RequestParameters) -> Bot:
        """
        Get bot.
        Permission: SADMIN, USER (owner)

        Args:
            id: bot id
            params: request parameters

        Returns: bot

        """
        bot = self.bots.get(id)
        if (
            bot
            and params.user
            and any(
                (
                    params.user.is_site_admin(),
                    params.user.is_himself(user=Identity(id=bot.owner)),
                )
            )
        ):
            return bot
        else:
            raise UserHasNotPermissionError()

    def get_all_bots_by_owner(
        self, owner: int, params: RequestParameters
    ) -> List[Bot]:
        """
        Get by bo owned by a user
        Permission: SADMIN, USER (owner)

        Args:
            owner: bots owner id
            params: request parameters

        Returns: list of bot owned by user

        """
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_himself(Identity(id=owner)),
            )
        ):
            return self.bots.get_all_by_owner(owner)
        else:
            raise UserHasNotPermissionError()

    def exists_bot(self, id: int) -> bool:
        """
        Check if bot exist.

        Args:
            id: bot id

        Returns: true if bot exist, false else.

        """
        return self.bots.exists(id)

    def authenticate(self, name: str, pwd: str) -> Optional[JWTUser]:
        """
        Check if password match username stored in DB.
        Args:
            name: username
            pwd: user password

        Returns: jwt data with user information if auth success, None else.

        """
        extern = self.ldap.login(name, pwd)
        if extern:
            return self.get_jwt(extern.id)

        intern = self.users.get_by_name(name)
        if intern and intern.password.check(pwd):  # type: ignore
            return self.get_jwt(intern.id)

        return None

    def get_jwt(self, user_id: int) -> Optional[JWTUser]:
        """
        Build a jwt data from user id.

        Args:
            user_id: user id

        Returns: jwt data with user information.

        """
        user = self.ldap.get(user_id) or self.users.get(user_id)
        if user:
            return JWTUser(
                id=user.id,
                impersonator=user.get_impersonator(),
                type=user.type,
                groups=[
                    JWTGroup(id=r.group.id, name=r.group.name, role=r.type)
                    for r in self.roles.get_all_by_user(user_id)
                ],
            )

        return None

    def get_all_groups(self, params: RequestParameters) -> List[Group]:
        """
        Get all groups.
        Permission: SADMIN
        Args:
            params: request parameters

        Returns: list of groups

        """
        if not params.user:
            raise UserHasNotPermissionError()

        if params.user.is_site_admin():
            return self.groups.get_all()
        else:
            roles_by_user = self.roles.get_all_by_user(user=params.user.id)
            groups = []
            for role in roles_by_user:
                tmp = self.groups.get(role.group_id)
                if tmp:
                    groups.append(tmp)
            return groups

    def get_all_users(self, params: RequestParameters) -> List[User]:
        """
        Get all users.
        Permission: SADMIN
        Args:
            params: request parameters

        Returns: list of groups

        """
        if params.user and params.user.is_site_admin():
            return self.ldap.get_all() + self.users.get_all()
        else:
            raise UserHasNotPermissionError()

    def get_all_bots(self, params: RequestParameters) -> List[Bot]:
        """
        Get all bots
        Permission: SADMIN
        Args:
            params: request parameters

        Returns:

        """
        if params.user and params.user.is_site_admin():
            return self.bots.get_all()
        else:
            raise UserHasNotPermissionError()

    def get_all_roles_in_group(
        self, group: str, params: RequestParameters
    ) -> List[Role]:
        """
        Get all roles inside a group
        Permission: SADMIN, GADMIN (own group)

        Args:
            group: group linked to role
            params: request parameters

        Returns: list of role

        """
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(Group(id=group)),
            )
        ):
            return self.roles.get_all_by_group(group)
        else:
            raise UserHasNotPermissionError()

    def delete_group(self, id: str, params: RequestParameters) -> None:
        """
        Delete group
        Permission: SADMIN, GADMIN (own group)
        Args:
            id: group id to delete
            params: request parameters

        Returns:

        """
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(Group(id=id)),
            )
        ):
            for role in self.roles.get_all_by_group(group=id):
                self.roles.delete(user=role.identity_id, group=role.group_id)

            return self.groups.delete(id)
        else:
            raise UserHasNotPermissionError()

    def delete_user(self, id: int, params: RequestParameters) -> None:
        """
        Delete user
        Permission: SADMIN, USER (own user)
        Args:
            id: user id
            params: request parameters

        Returns:

        """
        if params.user and any(
            (params.user.is_site_admin(), params.user.is_himself(User(id=id)))
        ):
            for b in self.bots.get_all_by_owner(id):
                # TODO : use cascade in the Role model definition
                for role in self.roles.get_all_by_user(user=b.id):
                    self.roles.delete(
                        user=role.identity_id, group=role.group_id
                    )
                self.delete_bot(b.id, params)

            # TODO : use cascade in the Role model definition
            for role in self.roles.get_all_by_user(user=id):
                self.roles.delete(user=role.identity_id, group=role.group_id)

            # self.ldap.delete(id)
            return self.users.delete(id)  # return for test purpose
        else:
            raise UserHasNotPermissionError()

    def delete_bot(self, id: int, params: RequestParameters) -> None:
        """
        Delete bot
        Permission: SADMIN, USER (owner)
        Args:
            id: bot id
            params: request parameters

        Returns:

        """
        bot = self.bots.get(id)
        if (
            params.user
            and bot
            and any(
                (
                    params.user.is_site_admin(),
                    params.user.is_himself(Identity(id=bot.owner)),
                )
            )
        ):
            return self.bots.delete(id)
        else:
            raise UserHasNotPermissionError()

    def delete_role(
        self, user: int, group: str, params: RequestParameters
    ) -> None:
        """
        Delete role
        Permission: SADMIN, GADMIN (own group)
        Args:
            user: user linked to role
            group: group linked to role
            params: request parameters

        Returns:

        """
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(Group(id=group)),
            )
        ):
            return self.roles.delete(user, group)
        else:
            raise UserHasNotPermissionError()

    def delete_all_roles_from_user(
        self, id: int, params: RequestParameters
    ) -> int:
        """
        Delete all roles from a specific user
        Permission: SADMIN, GADMIN (own group)
        Args:
            id: user linked to roles
            params: request parameters

        Returns:

        """
        roles = self.roles.get_all_by_user(id)
        groups = [r.group for r in roles]

        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(groups),
            )
        ):
            for role in roles:
                self.roles.delete(role.identity_id, role.group_id)
            return id
        else:
            raise UserHasNotPermissionError()
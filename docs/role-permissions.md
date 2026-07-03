# Vision Pass role permissions

## Permission matrix

| Capability | Super admin | Client admin | Tenant user |
|---|:---:|:---:|:---:|
| Platform dashboard and audit logs | Yes | No | No |
| Create/update/delete tenants | Yes | No | No |
| Manage master features | Yes | No | No |
| View own tenant dashboard | No | Yes | Personal only |
| Manage tenant members/features | No | Yes | No |
| Manage employees, shifts, holidays and settings | No | Yes | No |
| Enroll employee faces | No | Yes | No |
| Manage/test cameras | No | Yes | No |
| Manage visitors | No | Yes | No |
| Make/view access decisions | No | Yes | No |
| View/acknowledge/resolve alerts | No | Yes | No |
| View/export tenant reports | No | Yes | No |
| View own attendance/profile/notifications | No | Yes | Yes |

## Role names

The database enum currently stores client administrators as `tenant_admin` and
regular members as `user`. The frontend presents these as Client Admin and
Tenant User. `client_admin` is accepted by some authorization normalization
code for compatibility but is not a distinct persisted database role in the
current migration chain.

## Enforcement

Permissions are enforced in backend dependencies and tenant-scoped services;
frontend route guards are usability controls, not the security boundary.
Feature grants can further restrict a tenant or member. Inactive, deleted or
suspended accounts and inactive tenants are rejected before operational access.

"""Enterprise-core permission catalog (Phase 1).

These are software authorization constants (not fabricated domain values). They
are seeded into the global ``permission`` table by the onboarding service and
referenced by API guards.
"""

from __future__ import annotations

# Platform-level (cross-tenant) administration.
PLATFORM_TENANT_PROVISION = "platform.tenant.provision"

# Tenant-scoped IAM administration.
IAM_USER_READ = "iam.user.read"
IAM_USER_WRITE = "iam.user.write"
IAM_ROLE_READ = "iam.role.read"
IAM_ROLE_MANAGE = "iam.role.manage"

# Organizational structure.
ORG_UNIT_READ = "org.unit.read"
ORG_UNIT_WRITE = "org.unit.write"

# Agriculture master data + GIS (Phase 2).
AGRI_MASTERDATA_READ = "agri.masterdata.read"
AGRI_MASTERDATA_MANAGE = "agri.masterdata.manage"
AGRI_FARM_READ = "agri.farm.read"
AGRI_FARM_WRITE = "agri.farm.write"
AGRI_PARCEL_READ = "agri.parcel.read"
AGRI_PARCEL_WRITE = "agri.parcel.write"

# Full catalog seeded per environment.
ENTERPRISE_CORE_PERMISSIONS: dict[str, str] = {
    PLATFORM_TENANT_PROVISION: "Provision new tenants (platform administrators).",
    IAM_USER_READ: "Read users within the tenant.",
    IAM_USER_WRITE: "Create, update, and deactivate users.",
    IAM_ROLE_READ: "Read roles and permissions.",
    IAM_ROLE_MANAGE: "Create roles and grant/revoke permissions.",
    ORG_UNIT_READ: "Read organizational units.",
    ORG_UNIT_WRITE: "Create and modify organizational units.",
    AGRI_MASTERDATA_READ: "Read agriculture master/reference data.",
    AGRI_MASTERDATA_MANAGE: "Create and modify agriculture master data.",
    AGRI_FARM_READ: "Read farms.",
    AGRI_FARM_WRITE: "Create and modify farms.",
    AGRI_PARCEL_READ: "Read land parcels.",
    AGRI_PARCEL_WRITE: "Create and modify land parcels.",
}

# Permissions granted to the seeded TENANT_ADMIN system role (tenant-scoped;
# excludes platform-level provisioning).
TENANT_ADMIN_PERMISSIONS: tuple[str, ...] = (
    IAM_USER_READ,
    IAM_USER_WRITE,
    IAM_ROLE_READ,
    IAM_ROLE_MANAGE,
    ORG_UNIT_READ,
    ORG_UNIT_WRITE,
    AGRI_MASTERDATA_READ,
    AGRI_MASTERDATA_MANAGE,
    AGRI_FARM_READ,
    AGRI_FARM_WRITE,
    AGRI_PARCEL_READ,
    AGRI_PARCEL_WRITE,
)

TENANT_ADMIN_ROLE_CODE = "TENANT_ADMIN"
PLATFORM_ADMIN_ROLE_CODE = "PLATFORM_ADMIN"

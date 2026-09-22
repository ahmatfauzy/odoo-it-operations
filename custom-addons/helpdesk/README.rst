Helpdesk
========

A small Helpdesk module for Odoo 18 Community. It can be installed without
Odoo's Organization/HR modules and provides the models and screens needed to
start triaging tickets:

* ``helpdesk.ticket`` with ticket numbering, stages, teams, tags, priorities,
  SLA deadline and workflow fields;
* ``helpdesk.stage``, ``helpdesk.team`` and ``helpdesk.tag`` configuration
  models, with ``helpdesk.team.member_ids`` based directly on ``res.users``;
* kanban, list, form and search views, plus seeded New/In Progress/Resolved/
  Closed stages; and
* separate Helpdesk User and Helpdesk Manager roles.

Security and onboarding
-----------------------

Helpdesk Users can work with tickets visible through their assignment or team;
Helpdesk Managers can manage all tickets and configuration. Configuration
menus and model ACLs are not granted to ordinary internal users. An Odoo
administrator (``base.group_system``) is deliberately included in the Helpdesk
menus and has full model ACLs, so the module remains discoverable and
configurable during initial setup even before a Helpdesk role is assigned.

The normal setup flow is:

#. Install/upgrade the ``helpdesk`` module.
#. As an Odoo administrator, open **Helpdesk → Configuration → Teams** and
   create a team, then add internal users as members.
#. Assign **Helpdesk User** or **Helpdesk Manager** to the relevant users.
#. Create tickets from **Helpdesk → Tickets**.

The Docker development stack mounts this addon at ``/mnt/extra-addons``. To
upgrade the installed module in the development database:

.. code-block:: console

   docker compose exec web odoo -c /tmp/odoo.conf \
     --db_host=db --db_port=5432 --db_user="$POSTGRES_USER" \
     --db_password="$POSTGRES_PASSWORD" -d helpdesk_dev -u helpdesk \
     --stop-after-init

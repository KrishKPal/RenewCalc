# Tariff policy

This release deliberately has **zero** verified Indian DISCOM tariff records. The tariff lookup endpoint returns `unavailable`. In scenario mode the user specifies one energy import rate, optional monthly export credit rate and one fixed monthly charge.

The billing contract is clear: imports are billed at user rate; export credits may offset energy charges only and never fixed charges. Credits do **not** carry between months. No net-metering, slab-based duty, fuel adjustments, demand charges, subsidies or taxes are assumed.

A future verified tariff import requires source document, jurisdiction/utility/service territory, customer and voltage class, applicability dates, currency/units, fixed/demand/energy rates, adjustment rules, export settlement method and review time. Automated retrieval must not silently overwrite curated verified tariffs.

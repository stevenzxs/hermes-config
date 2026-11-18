# Baseline-preserving joint revision policy

Approved policy: server baseline 0.23.1, Android baseline 4.0.0 / 3049.
New joint packaging workflow runs allocate r1, r2, ...; failed runs consume
their revision. Re-running the same GitHub run ID reuses its assignment.
Preflight and progress queries never allocate. Both products share a revision.

Generated identities for r1:

- Server display: `0.23.1+r1`; image tag: `0.23.1-r1`.
- Android display: `4.0.0+r1`; Flutter declaration: `4.0.0+30491`.
- Android base code: decimal concatenation of `3049` and revision; existing
  ABI scheme remains base * 10 + ABI code. Reject overflow before allocation.

`linux/revision_versions.py` implements deterministic version derivation and
run-ID ledger validation. Its CLI requires an exclusive caller lock and a
trusted persistent ledger: it is NOT by itself a concurrency-safe allocator.
Never reconstruct the counter from only successful releases or retained runs.

## Integration gate (not yet enabled)

The existing workflows still use explicit version inputs. Do not describe the
new automatic policy as active until all following items have been implemented:

1. Serialize allocation and persist the append-only run-ID/revision mapping
   before product tests/builds; protect against stale ledgers and retries.
2. Create reviewed Android version commits without rewriting existing work;
   bind the generated version commit, original source SHA and configuration SHA.
3. Teach native Gradle and APK verification about committed revision metadata,
   preserving package identity, signing certificate, and source-asset checks.
4. Replace stale exact-3048 release tests with explicit baseline/revision and
   ABI upgrade-contract checks, without weakening historical identity tests.
5. Feed the same revision into server install stamp, image labels/tag and joint
   manifest. Check the user-facing runtime version, not only image labels.
6. Keep standalone Android dispatch from bypassing revision allocation; internal
   reusable builds consume the parent's assignment without allocating again.
7. Verify workflow wiring, permissions, retry and concurrent-dispatch behavior;
   only then run the separately approved Actions delivery acceptance.

No workflow is dispatched by the policy helper. No runtime configuration,
signing credentials, 150 controller or 115 deployment is changed.

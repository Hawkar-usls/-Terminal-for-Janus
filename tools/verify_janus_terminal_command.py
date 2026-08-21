#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

POLICY_PATH = Path('.janus/JANUS_TERMINAL_AUTHORITY_POLICY.json')


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError(f'{path}:JSON_OBJECT_REQUIRED')
    return value


def validate(policy: dict[str, Any], command: dict[str, Any], github_actor: str) -> dict[str, Any]:
    errors: list[str] = []
    req = policy['command_requirements']

    if github_actor not in policy.get('authorized_github_actors', []):
        errors.append('GITHUB_ACTOR_NOT_AUTHORIZED')
    if command.get('schema') != req['schema']:
        errors.append('COMMAND_SCHEMA_REJECT')
    if command.get('human_authorization') is not True:
        errors.append('EXPLICIT_HUMAN_AUTHORIZATION_REQUIRED')
    if command.get('requested_by') not in policy.get('human_aliases', []):
        errors.append('REQUESTED_BY_NOT_HUMAN_ROOT_ALIAS')
    if command.get('operation') not in policy.get('allowed_operations', []):
        errors.append('OPERATION_NOT_ALLOWLISTED')
    if command.get('authority') not in policy.get('allowed_authority_modes', []):
        errors.append('AUTHORITY_MODE_NOT_ALLOWLISTED')

    targets = command.get('targets')
    if not isinstance(targets, list) or not targets or not all(isinstance(t, str) and t.strip() for t in targets):
        errors.append('EXPLICIT_TARGETS_REQUIRED')
    else:
        owner_prefix = str(req.get('targets_default_owner_prefix', ''))
        for target in targets:
            repo = target.split('@', 1)[0]
            if owner_prefix and not repo.startswith(owner_prefix):
                errors.append(f'TARGET_OUTSIDE_DEFAULT_OWNER_SCOPE:{target}')

    if command.get('operation') == 'FIRST_LIVE_AURA_SPI_HABITAT_SPIRAL':
        if command.get('authority') != 'TEST_EXECUTION':
            errors.append('FIRST_LIVE_SPIRAL_REQUIRES_TEST_EXECUTION')
        if command.get('demihead_default') != 'HOLD':
            errors.append('FIRST_LIVE_SPIRAL_DEMIHEAD_MUST_HOLD')
        if command.get('intent_authority') != 'LOCAL_PREVIEW':
            errors.append('FIRST_LIVE_SPIRAL_INTENT_AUTHORITY_MUST_BE_LOCAL_PREVIEW')

    result = {
        'schema': 'janus.terminal.command_verification_receipt.v1',
        'policy_id': policy.get('policy_id'),
        'command_id': command.get('command_id'),
        'github_actor': github_actor,
        'authorized': not errors,
        'errors': errors,
        'control_principal': policy.get('control_principal'),
        'human_root': policy.get('human_root'),
        'terminal_is_truth_authority': False,
        'command_is_evidence': False,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description='Fail-closed JANUS Terminal command verifier')
    parser.add_argument('--command', type=Path, required=True)
    parser.add_argument('--policy', type=Path, default=POLICY_PATH)
    parser.add_argument('--github-actor', default=os.getenv('GITHUB_ACTOR', ''))
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()

    try:
        policy = load_json(args.policy)
        command = load_json(args.command)
        receipt = validate(policy, command, args.github_actor)
        text = json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
        if args.receipt:
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            args.receipt.write_text(text, encoding='utf-8')
        else:
            sys.stdout.write(text)
        return 0 if receipt['authorized'] else 3
    except Exception as exc:
        sys.stderr.write(f'verify_janus_terminal_command: {exc}\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

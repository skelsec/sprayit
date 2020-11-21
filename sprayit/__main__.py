import asyncio
import logging
from tqdm import tqdm
from sprayit import logger
from sprayit.sprayer import Sprayer
from sprayit.modules.ldap import LDAPSpray
from sprayit.common.targetgens.arghelper import get_targets, get_passwords, get_users


async def amain():
	import argparse

	parser = argparse.ArgumentParser(description='Pure Python implementation of Mimikatz --and more--')
	parser.add_argument('-v', '--verbose', action='count', default=0)
	parser.add_argument('-w', '--worker-count', type=int, default=4, help='Parallell count')
	parser.add_argument('--progress', action='store_true',  help='NOT IMPLEMENTED YET! Show progress')

	subparsers = parser.add_subparsers(help = 'module')
	subparsers.required = True
	subparsers.dest = 'module'
	
	ldap_group = subparsers.add_parser('ldap', help= 'LDAP module')
	ldap_group.add_argument('--authmethod', choices=['ntlm', 'sicily', 'plain'], default='ntlm', help='port')
	ldap_group.add_argument('-b', '--badpwcount', help='Bad password count allowed by the domain. Must be bigger than 2')
	ldap_group.add_argument('-l', '--lockout-treshold', help='Amount of time in secodsn of which th domain controller checks for bad passwords')
	ldap_group.add_argument('-d', '--domain', help='domain')
	ldap_group.add_argument('-u', '--user', action='append', help='Username or file with users')
	ldap_group.add_argument('-p', '--password', action='append',  help='Password or file qith passwords')
	ldap_group.add_argument('--users-from-module', action='store_true',  help='Get target users by using the LDAP URL')
	ldap_group.add_argument('--url', help='Connection URL base, target can be set to anything. Owerrides all parameter based connection settings! Example: "smb2+ntlm-password://TEST\\victim@test"')
	ldap_group.add_argument('--port', type=int, default=398, help='port')
	ldap_group.add_argument('--ldaps', action='store_true',  help='Use LDAP over SSL')
	ldap_group.add_argument('target', help = 'Hostname or IP address')

	args = parser.parse_args()
	
	
	###### VERBOSITY
	if args.verbose == 0:
		logging.basicConfig(level=logging.INFO)
	elif args.verbose == 1:
		logger.setLevel(logging.DEBUG)
	else:
		logger.setLevel(logging.DEBUG)
		logging.basicConfig(level=logging.DEBUG)

	if args.module == 'ldap':

		max_bad_password_cnt = int(args.badpwcount) if args.badpwcount is not None else 5
		lockout_treshold = int(args.lockout_treshold) if args.lockout_treshold is not None else 30

		progq = None
		if args.progress:
			progq = asyncio.Queue()

		tp = 'ldap' if args.ldaps is False else 'ldaps'
		module = LDAPSpray(args.url)
		target = LDAPSpray.build_taget_template(args.target, target_protocol=tp)
		sprayer = Sprayer(
			module, 
			target, 
			domain=args.domain, 
			users_from_module=args.users_from_module, 
			max_bad_password_cnt = max_bad_password_cnt, 
			lockout_treshold = lockout_treshold,
			progress_queue = progq,
		)
		get_passwords(args, sprayer)
		get_users(args, sprayer)

		if not args.progress:
			return await sprayer.run()
		else:
			main_task = asyncio.create_task(sprayer.run())
			# TODO


def main():
	asyncio.run(amain())
		

if __name__ == '__main__':
	main()
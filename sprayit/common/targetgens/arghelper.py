import sys

from sprayit.common.targetgens.file import FileTargetGen
from sprayit.common.targetgens.list import ListTargetGen


def get_targets(args, obj, throw = True):
	notfile = []
	if len(args.targets) == 0 and getattr(args, 'stdin', False) is True:
		obj.target_gens.append(ListTargetGen(sys.stdin))
	else:
		for target in args.targets:
			try:
				f = open(target, 'r')
				f.close()
				obj.target_gens.append(FileTargetGen(target))
			except:
				notfile.append(target)
		
	if len(notfile) > 0:
		obj.target_gens.append(ListTargetGen(notfile))

	if len(obj.target_gens) == 0 and throw is True:
		print('[-] No suitable targets were found!')
		return

def get_users(args, obj, throw = True):
	notfile = []
	if len(args.user) == 0 and getattr(args, 'stdin', False) is True:
		obj.user_gens.append(ListTargetGen(sys.stdin))
	else:
		for target in args.user:
			try:
				f = open(target, 'r')
				f.close()
				obj.user_gens.append(FileTargetGen(target))
			except:
				notfile.append(target)
		
	if len(notfile) > 0:
		obj.user_gens.append(ListTargetGen(notfile))

	if len(obj.user_gens) == 0 and throw is True:
		print('[-] No suitable users were found!')
		return

def get_passwords(args, obj, throw = True):
	notfile = []
	if len(args.password) == 0 and getattr(args, 'stdin', False) is True:
		obj.password_gens.append(ListTargetGen(sys.stdin))
	else:
		for target in args.password:
			try:
				f = open(target, 'r')
				f.close()
				obj.password_gens.append(FileTargetGen(target))
			except:
				notfile.append(target)
		
	if len(notfile) > 0:
		obj.password_gens.append(ListTargetGen(notfile))

	if len(obj.password_gens) == 0 and throw is True:
		print('[-] No suitable users were found!')
		return
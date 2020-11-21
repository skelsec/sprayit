from msldap.connection import MSLDAPClientConnection
from msldap.commons.credential import MSLDAPCredential, LDAPAuthProtocol
from msldap.commons.target import MSLDAPTarget, LDAPProtocol
from msldap.commons.url import MSLDAPURLDecoder

class LDAPSpray:
	def __init__(self, url = None):
		self.url = url
		self.client = None
		self.lockout_duration = 0
		self.lockout_observation = 0
		self.lockout_treshold = 9999
		self.minpwlen = 0

	async def get_lockout_treshold(self):
		return self.lockout_observation, None

	async def get_badpassword_max(self):
		return self.lockout_treshold, None

	async def get_users(self):
		if self.client is None:
			yield None, None, None
		else:
			yield None, None, NotImplementedError('')

	async def setup(self):
		try:
			if self.url is not None:
				self.client = MSLDAPURLDecoder(self.url).get_client()
				_, err = await self.client.connect()
				if err is not None:
					raise err
				
				adinfo, err = await self.client.get_ad_info()
				if err is not None:
					raise err
				if adinfo.lockoutDuration:
					self.lockout_duration = ((-1 * adinfo.lockoutDuration) // 10000000)
				if adinfo.lockOutObservationWindow:
					self.lockout_observation = ((-1 * adinfo.lockOutObservationWindow) // 10000000)
				if adinfo.lockoutThreshold:
					self.lockout_treshold = adinfo.lockoutThreshold
				self.minpwlen = adinfo.minPwdLength

			
			return True, None
		except Exception as e:
			return False, e

	@staticmethod
	def build_taget_template(target, target_protocol = 'ldap', target_port = 389, proxy = None):
		lproto = LDAPProtocol.TCP
		if target_protocol.lower() == 'ldap':
			lproto = LDAPProtocol.TCP
		elif target_protocol.lower() == 'ldaps':
			lproto = LDAPProtocol.SSL

		target = MSLDAPTarget(
			target,
			port = target_port, 
			proto = lproto, 
			tree = None, 
			proxy = proxy, 
			timeout = 10
		)
		return target

	@staticmethod
	def get_password_from_cred(cred):
		#because not all modules will have password as variable
		return cred.password

	@staticmethod
	def build_auth_template(domain, username, password, auth_protocol = 'ntlm'):
		aproto = LDAPAuthProtocol.NTLM_PASSWORD
		if auth_protocol.lower() == 'ntlm':
			aproto = LDAPAuthProtocol.NTLM_PASSWORD
		elif auth_protocol.lower() == 'sicily':
			aproto = LDAPAuthProtocol.SICILY
		elif auth_protocol.lower() == 'plain':
			aproto = LDAPAuthProtocol.PLAIN
		elif auth_protocol.lower() == 'simple':
			aproto = LDAPAuthProtocol.SIMPLE

		cred = MSLDAPCredential(
			domain=domain, 
			username= username, 
			password = password, 
			auth_method = aproto, 
			settings = None, 
			etypes = None)
		
		return cred
	
	async def try_credential(self, target, cred):
		connection = None
		try:
			
			connection = MSLDAPClientConnection(target, cred)
			_, err = await connection.connect()
			if err is not None:
				return False, 'CONNECTIONERR'
			_, err = await connection.bind()
			if err is not None:
				return False, 'CREDENTIALERR'
			return True, None
		except Exception as e:
			import traceback
			traceback.print_exc()
			return False, e
		
		finally:
			if connection is not None:
				try:
					await connection.disconnect()
				except:
					pass
		
		

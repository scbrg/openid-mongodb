"""MongoDB Store

This back-end is heavily based on the RedisStore from the openid-redis package.
"""
import time, logging
from openid.store import nonce
from openid.store.interface import OpenIDStore
from openid.association import Association
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

log = logging.getLogger(__name__)

__all__ = ["MongoDBStore"]

class MongoDBStore(OpenIDStore):

    def __init__(self, host="localhost", port=27017, db="openid", database=None,
                 associations_collection="associations", nonces_collection="nonces",
                 username=None, password=None):
        if database is not None:
            self._conn = database.connection
            self._db = database
        else:
            self._conn = MongoClient(host, port)
            self._db = self._conn[db]
        if username and password:
            self._db.authenticate(username, password)
        self.associations = self._db[associations_collection]
        self.nonces = self._db[nonces_collection]
        super(MongoDBStore, self).__init__()

    def storeAssociation(self, server_url, association):
        log.debug("Storing association for server_url: %s, with handle: %s",
                  server_url, association.handle)
        if server_url.find('://') == -1:
            raise ValueError('Bad server URL: %r' % server_url)
        self.associations.insert_one({
            "_id": hash((server_url, association.handle)),
            "server_url": server_url,
            "handle": association.handle,
            "association": association.serialize(),
            "expires": time.time() + association.expiresIn
        })

    def getAssociation(self, server_url, handle=None):
        log.debug("Association requested for server_url: %s, with handle: %s",
                  server_url, handle)
        if server_url.find('://') == -1:
            raise ValueError('Bad server URL: %r' % server_url)
        if handle is None:
            associations = self.associations.find({
                "server_url": server_url
            })
            if associations.count():
                associations = [Association.deserialize(a['association'])
                                for a in associations]
                # Now use the one that was issued most recently
                associations.sort(cmp=lambda x, y: cmp(x.issued, y.issued))
                log.debug("Most recent is %s", associations[-1].handle)
                return associations[-1]
        else:
            association = self.associations.find_one({
                "_id": hash((server_url, handle)),
                "server_url": server_url,
                "handle": handle
            })
            if association:
                return Association.deserialize(association['association'])

    def removeAssociation(self, server_url, handle):
        log.debug('Removing association for server_url: %s, with handle: %s',
                  server_url, handle)
        if server_url.find('://') == -1:
            raise ValueError('Bad server URL: %r' % server_url)
        res = self.associations.delete_one({"_id": hash((server_url, handle)),
                                            "server_url": server_url,
                                            "handle": handle})
        return bool(res.deleted_count)

    def cleanupAssociations(self):
        r = self.associations.delete_many({"expires": {"$gt": time.time()}})
        return r.deleted_count

    def useNonce(self, server_url, timestamp, salt):
        if abs(timestamp - time.time()) > nonce.SKEW:
            log.debug('Timestamp from current time is less than skew')
            return False

        n = hash((server_url, timestamp, salt))
        try:
            self.nonces.insert_one({"_id": n,
                                    "server_url": server_url,
                                    "timestamp": timestamp,
                                    "salt": salt})
        except DuplicateKeyError, e:
            log.debug('Nonce already exists: %s', n)
            return False
        else:
            return True

    def cleanupNonces(self):
        r = self.nonces.delete_many(
            {"$or": [{"timestamp": {"$gt": time.time() + nonce.SKEW}},
                     {"timestamp": {"$lt": time.time() - nonce.SKEW}}]},
            safe=True)
        return r.deleted_count

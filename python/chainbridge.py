#!/usr/bin/python3

from collections.abc import Iterable
from decimal import Decimal
from os.path import isfile
import pickle
import requests
from time import sleep, time



class ResponseObject(object):
    """
    This class holds response data of an API query
    """



    def __init__(self, code=None, content=None):
        """
        Initializes the ResponseObject
        ==============================


        Parameters
        ----------
        code : int, optional (None if omitted)
            The return code of a response. Having a return code of 200 usually
            means that everything went just fine. Having a return code different
            than 200 are usually proof of error.
        content : dict, list, optional (None if omitted)
            The returned data of a response. Common usage of this object can be
            sending of JSON based data which is transformed into a structured
            Python variable. Variables deserialized from JSON used to be a mix
            of list and dict instances.

        Attributes
        ----------

        code
        content
        """

        self.__code = None
        self.__content = None
        self.code = code
        self.content = content



    @property
    def code(self):
        """
        Returns the status code of a request
        ====================================

        Returns
        -------
        int, None
            Status code, if already not set, the status code is none.
        """

        return self.__code



    @code.setter
    def code(self, newcode):
        """
        Sets the request's status code
        ==============================

        Parameters
        ----------
        newcode : int
            Code to set as response status code. This value can be set at once
            only on an instance.

        Throws
        ------
        PermissionError
            If tried to set a response code when it is different than None.
        """

        if self.__code is None:
            self.__code = newcode
        else:
            raise PermissionError('Tried to overwrite an existing response code.')



    @property
    def content(self):
        """
        Returns the content of the response
        ===================================

        Returns
        -------
        any
            The content of the response. The content itself used to be a mix of
            lists and dictionaries since JSON is a quite common response format
            and Python interprets those string into types mentioned above.
        """

        return self.__content



    @content.setter
    def content(self, newcontent):
        """
        Sets the content of the response
        ================================

        Parameters
        ----------
        newcontent : any
            The content of the request's response. It can be any type, bit a mix
            of list and dict instances are quite common in case of API services,
            because they are using JSON to serialize data.
        """

        if self.__content is None:
            self.__content = newcontent
        else:
            raise PermissionError('Tried to overwrite an existing response content.')



class APIHandler(object):
    """
    This class helps to manage SEO style REST API queries in a convinient way
    """



    DEFAULT_TRY_COUNT = 5
    DEFAULT_TRY_DELAY = 5000



    def __init__(self, api_root, try_count=None, try_delay=None, returncode_list=[]):
        """
        Initializes APIHandler object
        =============================

        Parameters
        ----------
        api_root : string
            The URL base of the future API queries. Due to the habit of the
            Python's request library, http://, https:// or other supported
            qualifiers couldn't be omitted.
        try_count : int, optional (None if omitted)
            Number of tries to have a sucessful query. If the value of this
            parameter omitted the value of DEFAULT_TRY_COUNT is used.
        try_delay : int, optional (None if omitted)
            Number of milliseconds to have a new try with the same query. If the
            value of this parameter is omitted the value of DEFAULT_TRY_DELAY
            is used instead.
        returncode_list : list of int, optional (empty list if omitted)
            This parameter lets the user to select error codes to accept, send
            back. By default request have result in case only, when return code
            from the server is 200. Adding elements to this parameter will cause
            that some error codes are sent back as result.
        """

        self.__api_root = api_root.rstrip('/')
        if try_count is None:
            self.try_count = APIHandler.DEFAULT_TRY_COUNT
        else:
            self.try_count = try_count
        if try_delay is None:
            self.try_delay = APIHandler.DEFAULT_TRY_DELAY
        else:
            self.try_delay = try_delay
        self.returncode_list = returncode_list



    @property
    def api_root(self):
        """
        Returns the API root
        ====================

        string
            The API root.
        """

        return self.__api_root



    def query(self, paramlist):
        """
        Makes a query from the API
        ==========================

        Parameters
        ----------
        paramlist : list of strings
            The content of paramlist is transformed into SEO friendly API
            query string. This means elements of the list gets joined together
            with a slash seperator.

        Returns
        -------
        ResponseObject
            If the query is successful a full ResponseObject instance is
            returned with content.
        ResponseObject (.content=errorcode; .content=None)
            If there is a list of acceptable error codes and the query ends with
            that error code, the returned ResponseObject has a .content
            attribute with None value and a code attribute with the received
            error code.
        None
            In case of total unsuccess the value of the return is None.

        Notes
        -----
            This method is a wrapper of the .query_() method. For common use
            cases the use of this method is preferred because of its user
            friendlynes.

        See Also
        --------
            To have more impression about the result of this method please
            consult the docs of the .query_() method too.
        """

        query_string = ''
        for param in paramlist:
            query_string += '/{}'.format(param)
        return self.query_(query_string)



    @property
    def returncode_list(self):
        """
        Gets the list of acceptable return codes
        ========================================

        Returns
        -------
        list of int
            List of acceptable error codes given by the user.

        Notes
        -----
            However 200 is an accepted return code it shouldn't be pert of that
            list because it's the default return code for success.
        """

        return self.__returncode_list



    @returncode_list.setter
    def returncode_list(self, newlist):
        """
        Sets the list of acceptable return codes
        ========================================

        Parameters
        ----------
        newlist : list of int
            Replaces the list of acceptable return codes.

        Notes
        -----
        1.
            200 is always accepted as this is the return code of success.
        2.
            In case if the modification of the returncode_list is temporary, the
            original value should be saved and reset.

        Example
        -------
            # To check whether a page exists or not the following example is
            # quite simple.

            handler = APIHandler('example.com')

            # ...

            # Check if page exists

            old_list = handler.returncode_list
            handler.returncode_list = [404]
            data = handler.query(['example'])
            if data is not None:
                if data.code === 200:
                    print('Page exists.')
                if data.code == 404:
                    print('Page doesn\'t exist.')
            else:
                print('Other error happen.')
            handler.returncode_list = old_list
        """

        self.__returncode_list = newlist



    @property
    def try_count(self):
        """
        Gets the amount of tries made in case of unsuccess
        ==================================================

        Returns
        -------
        int
            Number of tries.
        """

        return self.__try_count



    @try_count.setter
    def try_count(self, try_count):
        """
        Sets the number of tries in case of unsuccess
        =============================================

        Parameters
        ----------
        try_count : int
            The number of total tries in case of unsuccess.
        """

        self.__try_count = try_count



    @property
    def try_delay(self):
        """
        Gets the delay between requests in case of unsuccess
        ====================================================

        Returns
        -------
        int
            Delay in milliseconds.
        """

        return int(self.__try_delay * 1000)



    @try_delay.setter
    def try_delay(self, try_delay):
        """
        Sets the delay between requests in case of unsuccess
        ====================================================

        Parameters
        ----------
        try_delay : int
            Delay in milliseconds.
        """

        self.__try_delay = try_delay / 1000



    def query_(self, query_string):
        """
        Processes an actual query
        =========================

        Parameters
        ----------
        query_string : str
            String to be added to the API root to make a query.

        Returns
        -------
        ResponseObject
            If the query is successful a full ResponseObject instance is
            returned with content.
        ResponseObject (.content=errorcode; .content=None)
            If there is a list of acceptable error codes and the query ends with
            that error code, the returned ResponseObject hes a .content
            attribute with None value and a code attribute with the received
            error code.
        None
            In case of total unsuccess the value of the return is None.

        Notes
        -----
            The use of .query() method is preferred.

        See Also
        --------
            Please consult the documentation for .query() before the use of this
            method.
        """

        request_string = self.api_root + query_string
        do_loop = True
        try_counter = 0
        while do_loop:
            try_counter += 1
            request_success = True
            try:
                response = requests.get(request_string)
            except Exception:
                request_success = False
            if request_success:
                if response.status_code == 200:
                    json_success = True
                    try:
                        json_data = response.json()
                    except Exception:
                        json_success = False
                    if json_success:
                        return ResponseObject(200, json_data)
                elif response.status_code in self.returncode_list:
                    return ResponseObject(response.status_code, None)
            if try_counter >= self.try_count:
                do_loop = False
            else:
                sleep(self.__try_delay)



class BitcoinAPI(APIHandler):
    """
    This class provides simple interface to bitcoin.com REST API
    =============================================================

    Notes
    -----
        This object doesn't implement all the functionality of the bitcoin.com
        blockhain explorer API. It implements only those, which are needed to
        serve the purposes of ChainBridge.

    See Also
    --------
        Documentation of the bitcoin.com REST API can be consulet at:
        https://rest.bitcoin.com/
    """



    def __init__(self, try_count=None, try_delay=None):
        """
        Initializes the BitcoinAPI object
        =================================

        Parameters
        ----------
        try_count : int, optional (None if omitted)
            Number of tries to have a sucessful query. If the value of this
            parameter omitted the value of DEFAULT_TRY_COUNT is used.
        try_delay : int, optional (None if omitted)
            Number of milliseconds to have a new try with the same query. If the
            value of this parameter is omitted the value of DEFAULT_TRY_DELAY
            is used instead.

        Classmethods
        ------------
        address_from_public_key
        is_valid_wallet
        """

        super(self.__class__, self).__init__('http://rest.bitcoin.com/v2',
                                             try_count, try_delay, [400])



    @classmethod
    def address_from_public_key(cls, key):
        """
        Gets bitcoincash address from public key
        ========================================

        Parameters
        ----------
        key : str
            The string of a known public key to query.

        Returns
        -------
        str
            The bitcoincash address of the wallet.
        None
            If there is no address behind the public key or if the query
            wasn't successful at all.

        Notice
        ------
            This is a classmethod you can call it without instantiating a
            BitcoinAPI object.

        Example
        -------
            # Get the address that belongs to a known public key.

            data = BitcoinAPI.address_from_public_key('XXX')
            if data is not None:
                print('The address is: {}'.format(data))
            else:
                print('This key doesn\'t lead to a valid address or some error happened.')
        """

        api = APIHandler('http://rest.bitcoin.com/v2', returncode_list=[400])
        result = api.query(['address', 'fromXPub', key])
        if result is not None:
            if result.code == 200:
                if isinstance(result.content, dict):
                    if 'cashAddress' in result.content.keys():
                        return result.content['cashAddress']
        return None



    def get_address_details(self, walletaddress):
        """
        Gets the details record of the address
        ======================================

        Parameters
        ----------
        walletaddress : str
            The bitcoincash address of the wallet.

        Returns
        -------
        dict
            The details record that belongs to the given wallet.

        Throws
        ------
        ValueError
            If the given address is not valid.

        Notes
        -----
            The service works with legacy and SLP addresses as well but this
            code prefers to use bitcoincash address where possible.
        """

        data = self.query(['address', 'details', walletaddress])
        if data is not None:
            if data.code == 200:
                return data.content
            elif data.code == 400:
                raise ValueError('BitcoinAPI received invalid wallet address.')
        return None



    def get_address_transactions(self, walletaddress):
        """
        Gets transaction records of the address
        =======================================

        Parameters
        ----------
        walletaddress : str
            The bitcoincash address of the wallet.

        Returns
        -------
        dict
            List of all transactions that belongs to the given wallet.

        Throws
        ------
        ValueError
            If the given address is not valid.
        RuntimeError
            If the address gets invalid during pagination of the transaction list.
        RuntimeError
            If error, other than invalid user occures during the pagination of
            the transaction list.

        Notes
        -----
            The service works with legacy and SLP addresses as well but this
            code prefers to use bitcoincash address where possible.
        """

        data = self.query(['address', 'transactions', walletaddress])
        if data is not None:
            if data.code == 200:
                pages_count = data.content['pagesTotal']
                result = []
                for transaction in data.content['txs']:
                    result.append(transaction)
                for i in range(1, pages_count):
                    data = self.query(['address', 'transactions',
                                       '{}?page={}'.format(walletaddress, i)])
                    if data is not None:
                        if data.code == 200:
                            for transaction in data.content['txs']:
                                result.append(transaction)
                        else:
                            raise RuntimeError('BitcoinAPI - error 400 while getting address related transactions (page: {}/{}).'
                                               .format(i, pages_count))
                    else:
                        raise RuntimeError('BitcoinAPI - error while getting address related transactions (page: {}/{}).'
                                           .format(i, pages_count))
                return result
            elif data.code == 400:
                raise ValueError('BitcoinAPI received invalid wallet address.')
        return None



    def get_address_unconfirmed(self, walletaddress):
        """
        Gets the list of unconfirmed utxos of the address
        =================================================

        Parameters
        ----------
        walletaddress : str
            The bitcoincash address of the wallet.

        Returns
        -------
        dict
            The list of unconfirmed utxos that belongs to the given wallet.

        Throws
        ------
        ValueError
            If the given address is not valid.

        Notes
        -----
            The service works with legacy and SLP addresses as well but this
            code prefers to use bitcoincash address where possible.
        """

        data = self.query(['address', 'unconfirmed', walletaddress])
        if data is not None:
            if data.code == 200:
                return data.content['utcos']
            elif data.code == 400:
                raise ValueError('BitcoinAPI received invalid wallet address.')
        return None



    def get_address_utxo(self, walletaddress):
        """
        Gets the list of confirmed utxos of the address
        ===============================================

        Parameters
        ----------
        walletaddress : str
            The bitcoincash address of the wallet.

        Returns
        -------
        dict
            The list of confirmed utxos that belongs to the given wallet.

        Throws
        ------
        ValueError
            If the given address is not valid.

        Notes
        -----
            The service works with legacy and SLP addresses as well but this
            code prefers to use bitcoincash address where possible.
        """

        data = self.query(['address', 'utxo', walletaddress])
        if data is not None:
            if data.code == 200:
                return data.content['utxos']
            elif data.code == 400:
                raise ValueError('BitcoinAPI received invalid wallet address.')
        return None



    def get_block_by_hash(self, hash):
        """
        Gets the block data with the given hash
        =======================================

        Parameters
        ----------
        hash : str
            The hash of the bitcoincash block.

        Returns
        -------
        dict
            The full record of the block.

        Throws
        ------
        ValueError
            If the given hash is not valid.
        """

        data = self.query(['block', 'detailsByHash', hash])
        if data is not None:
            if data.code == 200:
                return data.content
            elif data.code == 400:
                raise ValueError('BitcoinAPI received invalid block hash.')
        return None



    def get_block_by_hight(self, hight):
        """
        Gets the block data with the given height
        ========================================

        Parameters
        ----------
        height : int, str
            The height of the bitcoincash block.

        Returns
        -------
        dict
            The full record of the block.

        Throws
        ------
        ValueError
            If the given height is not valid.
        """

        data = self.query(['block', 'detailsByHeight', hight])
        if data is not None:
            if data.code == 200:
                return data.content
            elif data.code == 400:
                raise ValueError('BitcoinAPI received invalid block height.')
        return None



    def get_transaction(self, txid):
        """
        Gets the transaction data with the given txid
        =============================================

        Parameters
        ----------
        txid : str
            The txid of the bitcoincash transaction.

        Returns
        -------
        dict
            The full record of the transaction.

        Throws
        ------
        ValueError
            If the given txid is not valid.
        """

        data = self.query(['transaction', 'details', txid])
        if data is not None:
            if data.code == 200:
                return data.content
            elif data.code == 400:
                raise ValueError('BitcoinAPI received invalid txid.')
        return None




    @classmethod
    def is_valid_wallet(cls, walletaddress):
        """
        Checks whether the address is valid or not
        ==========================================

        Parameters
        ----------
        walletaddress : str
            The bitcoincash address of the wallet.

        Returns
        -------
        bool
            True if the address is valid, False if not or if something error happen.

        Notes
        -----
        1.
            This is a classmethod you can call it without instantiating a
            BitcoinAPI object.
        2.
            The service works with legacy and SLP addresses as well but this
            code prefers to use bitcoincash address where possible.

        Example
        -------
            # Check a bitcoincash address
            if BitcoinAPI.is_valid_wallet('bitcoincash:XXX'):
                print('This is a valid address.')
            else:
                print('This address seems to be non-valid.')
        """

        api = APIHandler('http://rest.bitcoin.com/v2', returncode_list=[400])
        result = api.query(['address', 'details', walletaddress])
        if result is not None:
            if result.code == 200:
                return True
        return False



class Wallet(object):
    """
    This class provides basic functionality of a wallet
    """



    WALLET_INSTANTIATED = 0
    WALLET_VALID = 1
    WALLET_EDITABLE = 2



    def __init__(self, address=None, displayed_name=None, details=None):
        """
        Initializes the Wallet object
        =============================

        Parameters
        ----------
        address : str, optional (None if omitted)
            The address of the wallet instance.
        displayed_name : str, optional (None if omitted)
            The name to display for the wallet.
        details : dict, optional (None if omitted)
            Key, values pairs (str, str) of information about the wallet.

        Attributes
        ----------
        address
        details
        displayed_name
        state

        Class Level Constants
        ---------------------
        WALLET_INSTANTIATED
        WALLET_VALID
        WALLET_EDITABLE
        """

        self.__address = None
        self.__displayed_name = None
        self.__details = {}
        self.__state = Wallet.WALLET_INSTANTIATED
        self.state_add(Wallet.WALLET_EDITABLE)
        self.address = address
        self.displayed_name = displayed_name
        if details is not None:
            for key, value in details:
                self.set_detail(key, value)
        self.state_delete(Wallet.WALLET_EDITABLE)



    @property
    def address(self):
        """
        Gets the address of the wallet
        ==============================

        Returns:
        str
            The address of the wallet.
        """

        return self.__address



    @address.setter
    def address(self, address):
        """
        Sets the address of the wallet
        ==============================

        Parameters
        ----------
        address : str
            The address to be set as a wallet address.

        Throws
        ------
        PermissionError
            If you try to set the address more than once.
        PermissionError
            If the sate of the wallet doesn't cont WALLET_EDITABLE turned on.
        """

        if has_state(self.__state, Wallet.WALLET_EDITABLE):
            if self.__address is None:
                self.__address = address
                if BitcoinAPI.is_valid_wallet(address):
                    self.state_add(Wallet.WALLET_VALID)
            else:
                raise PermissionError('Tried to set read-only property "address".')
        else:
            raise PermissionError('Tried to change address of a non-editable wallet.')



    @property
    def details(self):
        """
        Gets all details of the wallet
        ==============================

        Returns
        -------
        dict
            Dict of details of the wallet.
        """

        return self.__details



    @property
    def displayed_name(self):
        """
        Gets the displayed name of the wallet
        =====================================

        Returns
        -------
        str
            The name that belongs to the wallet.
        """

        return self.__displayed_name



    @displayed_name.setter
    def displayed_name(self, name):
        """
        Sets the displayed name of the wallet
        =====================================

        Parameters
        ----------
        name : str
            The name that belongs to the wallet.

        Throws
        ------
        PermissionError
            If the Wallet doesn't have WALLET_EDITABLE state.
        """

        if has_state(self.__state, Wallet.WALLET_EDITABLE):
            if self.__displayed_name is None:
                self.__displayed_name = name
            else:
                if has_state(self.__state, Wallet.WALLET_EDITABLE):
                    self.__displayed_name = name
        else:
            raise PermissionError('Tried to change displayed name of a non-editable wallet.')



    def get_detail(self, key):
        """
        Gets a detail of the wallet
        ===========================

        Parameters
        ----------
        key : str
            The name of the detail to get.

        Returns
        -------
        str
            The value of the given detail.
        None
            If the given key doesn't exist, the returned value is None.
        """

        if key in self.__details:
            return self.__details[key]
        return None



    def set_detail(self, key, value):
        """
        Sets a detail of the wallet
        ===========================

        Parameters
        ----------
        key : str
            The name of the detail to set.
        value : str
            The new value of the given detail.

        Throws
        ------
        PermissionError
            If the Wallet doesn't have WALLET_EDITABLE state.
        """

        if has_state(self.__state, Wallet.WALLET_EDITABLE):
            self.__details[key] = value
        else:
            raise PermissionError('Tried to change a detail of a non-editable wallet.')



    @property
    def state(self):
        """
        Gets the cummulated state of the wallet
        =======================================

        Returns
        -------
        int
            The cummulated state of the wallet.

        Notes
        -----
            State can consist of the presense or lack of the following constants:
                WALLET_INSTANTIATED
                WALLET_VALID
                WALLET_EDITABLE
        """

        return self.__state



    def state_add(self, stateid):
        """
        Adds the given state type to the wallet
        =======================================

        Parameters
        ----------
        stateid : int
            State type to add to the state of the object.

        Throws
        ------
        ValueError
            If the given state type is not a valid Wallet state type.

        Notes
        -----
            State types can be:
                WALLET_INSTANTIATED
                WALLET_VALID
                WALLET_EDITABLE
        """

        if stateid in [Wallet.WALLET_VALID, Wallet.WALLET_EDITABLE]:
            if not has_state(self.__state, stateid):
                self.__state += stateid
        else:
            raise ValueError('Tried to add unknown state to a Wallet instance.')



    def state_delete(self, stateid):
        """
        Deletes the given state type from the wallet
        ==========================================

        Parameters
        ----------
        stateid : int
            State type to delete from the state of the object.

        Throws
        ------
        ValueError
            If the given state type is not a valid Wallet state type.

        Notes
        -----
            State types can be:
                WALLET_INSTANTIATED
                WALLET_VALID
                WALLET_EDITABLE
        """

        if stateid in [Wallet.WALLET_VALID, Wallet.WALLET_EDITABLE]:
            if has_state(self.__state, stateid):
                self.__state -= stateid
        else:
            raise ValueError('Tried to add unknown state to a Wallet instance.')



    def state_toggle(self, stateid):
        """
        Toggles the given state type of the wallet
        ==========================================

        Parameters
        ----------
        stateid : int
            State type to toggle in the state of the object.

        Throws
        ------
        ValueError
            If the given state type is not a valid Wallet state type.

        Notes
        -----
            State types can be:
                WALLET_INSTANTIATED
                WALLET_VALID
                WALLET_EDITABLE
        """

        if stateid in [Wallet.WALLET_VALID, Wallet.WALLET_EDITABLE]:
            if has_state(self.__state, stateid):
                self.__state -= stateid
            else:
                self.__state += stateid
        else:
            raise ValueError('Tried to add unknown state to a Wallet instance.')



class UserWallet(Wallet):
    """
    This class represents a user account and wallet
    """



    def __init__(self, address, displayed_name=None, details=None,
                 addressbook=None, documents=None, searches=None,
                 transactions=None, utxos=None, unconfirmed_utxos=None):
        """
        Intializes the UserWallet object
        ================================

        Parameters
        ----------
        address : str
            A bitcoincash address to register the user wallet to.
        displayed_name : str, optional (None if omitted)
            The name of the user to be displayed.
        details : dict, optional (None if omitted)
            Data in key, value (str, str) format that represents details of the
            user wallet.
        addressbook : WalletContainer, optional (None if omitted)
            Container of foreign wallets that are registered by the user.
        documents : list, optional (None if omitted)
            Container of the document that are made by the user.
        searches : list, optional (None if omitted)
            Container of search activities of the user.
        transaction : TransactionContainer, optional (None if omitted)
            Container of all transactions of the user.
        utxos : UtxoContainer, optional (None if omitted)
            Container of all confirmed utxos of the user.
        unconfirmed_utxos : UtxoContainer, optional (None if omitted)
            Container of all unconfirmed utxos of the user.

        Attributes
        ----------
        addressbook
        documents
        documents
        searches
        transactions
        utxos
        unconfirmed_utxos

        Classmethods
        ------------
        from_address
        from_file
        from_dict_

        Notes
        -----
        1.
            In contrast with common routines the creation of the UserWallet
            object through the usual init process is not suggested since
            it is not practical at all. Classmethods .from_address() and
            .from_file() provides much more convenient way to do this.
        2.
            However both .from_address() and .from_file() are actually wrappers
            of .from_dict_() classmethod it is strongly unadvised to use it
            directly. On the other hand for those who understand the workflow
            of the method it can be a good entry point to implement other ways
            to construct/restore an UserWallet instance.
        """

        super(self.__class__, self).__init__(address=address,
                                             displayed_name=displayed_name,
                                             details=details)
        if addressbook is None:
            self.__addressbook = WalletContainer()
        else:
            self.__addressbook = addressbook
        if documents is None:
            self.__documents = []
        else:
            self.__documents = documents
        if searches is None:
            self.__searches = []
        else:
            self.__searches = searches
        if transactions is None:
            self.__transactions = TransactionContainer()
        else:
            self.__transactions = transactions
        if utxos is None:
            self.__utxos = UtxoContainer()
        else:
            self.__utxos = utxos
        if unconfirmed_utxos is None:
            self.__unconfirmed_utxos = UtxoContainer()
        else:
            self.__unconfirmed_utxos = unconfirmed_utxos



        @property
        def addressbook(self):
            """
            Gets the addressbook of the user
            ================================

            Returns
            -------
            WalletContainer
                The addressbook of the user.

            Notes
            -----
                However this property does not have setter, it doesn't mean that
                the addressbook itself is not editable. It means only that it is
                not replaceable.
            """

            return self.__addressbook



        @property
        def documents(self):
            """
            Gets the list of the documents created by the user
            ==================================================

            Returns
            -------
            list
                The list of the documents of the user.

            Notes
            -----
                However this property does not have setter, it doesn't mean that
                the list of documents itself is not editable. It means only that
                it is not replaceable.
            """

            return self.__documents



        @classmethod
        def from_address(cls, address):
            """
            Creates a new UserWallet instance from bitcoincash address
            ==========================================================

            Parameters
            ----------
            address : str
                A bitcoincash address to create a new UserWallet from.

            Returns
            -------
            UserWallet
                The new instance for the user.

            Throws
            ------
            ValueError
                If the address is not valid.

            Notes
            -----
            1
                This is a classmethod and this method is a quite common and
                convenient way to create a user wallet especially if you use
                this code like part of online service and you register a new
                user.
            2
                The service works with legacy and SLP addresses as well but this
                code prefers to use bitcoincash address where possible.
            """

            data = {}
            pass
            return UserWallet.from_dict_(data)



        @classmethod
        def from_file(cls, filename):
            """
            Creates a new UserWallet instance from data from file
            =====================================================

            Parameters
            ----------
            filename : str
                The name or path of a file to create a new UserWallet from.

            Returns
            -------
            UserWallet
                The new instance for the user.

            Throws
            ------
            FileNotFoundError
                If the file does not exist.

            Notes
            -----
                This is a classmethod and this method is a quite common and
                convenient way to create a user wallet especially if you use
                this code like part of any service if you want to restore a user
                from a saved state.
            """

            if isfile(filename):
                with open(filename, 'rb') as instream:
                    data = pickle.load(instream)
                return UserWallet.from_dict_(data)
            else:
                raise FileNotFoundError('UserWallet.from_file() given fiel "{}" not found.'
                                        .format(filename))



        @property
        def searches(self):
            """
            Gets the list of the search experements created by the user
            ============================================================

            Returns
            -------
            list
                The list of the search experiments of the user.

            Notes
            -----
                However this property does not have setter, it doesn't mean that
                the list of searches itself is not editable. It means only that
                it is not replaceable.
            """

            return self.__searches



        @property
        def transactions(self):
            """
            Gets the transactions of the user
            =================================

            Returns
            -------
            TransactionContainer
                The transactions of the user.

            Notes
            -----
            1.
                However this property does not have setter, it doesn't mean that
                the transaction itself is not editable. It means only that it is
                not replaceable.
            2.
                It is strongly unadvised to delete from containers based on
                blockchain data. It is much better to re-query and re-generate
                the concerning object if something bad or unexpected happened.
            """

            return self.__transactions



        @property
        def utxos(self):
            """
            Gets the utxos of the user
            ================================

            Returns
            -------
            UtxoContainer
                The utxos of the user.

            Notes
            -----
            1.
                However this property does not have setter, it doesn't mean that
                the utxos itself is not editable. It means only that it is not
                replaceable.
            2.
                It is strongly unadvised to delete from containers based on
                blockchain data. It is much better to re-query and re-generate
                the concerning object if something bad or unexpected happened.
            """

            return self.__utxos


        @property
        def unconfirmed_utxos(self):
            """
            Gets the unconfirmed utxos of the user
            ======================================

            Returns
            -------
            UtxoContainer
                The unconfirmed utxos of the user.

            Notes
            -----
            1.
                However this property does not have setter, it doesn't mean that
                the unconfirmed utxos itself is not editable. It means only that
                it is not replaceable.
            2.
                It is strongly unadvised to delete from containers based on
                blockchain data. It is much better to re-query and re-generate
                the concerning object if something bad or unexpected happened.
            """

            return self.__unconfirmed_utxos




        @classmethod
        def from_dict_(cls, datadict):
            """
            Creates a new UserWallet instance from a dict
            =============================================

            Parameters
            ----------
            datadict : dict
                All the data which is needed to restore an existing UserWallet
                instance.

            Returns
            -------
            UserWallet
                The new instance for the user.

            Notes
            -----
                However this is a publicly accessible classmethod it is unadvised
                to use it directly for getting new UserWallet instances. On the
                other hand this method can be useful to restore UserWallet
                instances from different sources as well.
            """

            pass
            wallet = UserWallet()
            return wallet



class WalletContainer(list):
    """
    This class provides special container for Wallet instances

    Notes
    -----
        The purpose of this class is not contain UserWallet instances but to
        contain Wallet instances for an addressbook in a UserWallet instance.
    """



    def __init__(self, wallets=None):
        """
        Intializes the WalletContainer object
        =====================================

        Parameters
        ----------
        wallets : list
            List of wallets to add to the container right at instantiation.

        Notes
        -----
            WalletContainer is a subclass of list, please keep this in mind if
            you are using an instance of this class.
        """

        add_wallets = True
        if wallets is None:
            add_wallets = False
        elif isinstance(wallets, Iterable):
            for Wallet in wallets:
                if not isinstance(wallet, Wallet):
                    add_wallets = False
                    break
        if add_wallets:
            super(self.__class__, self).__init__(wallets)
        else:
            super(self.__class__, self).__init__()



    def append(self, item):
        """
        Appends a new item to the WalletContainer
        =========================================

        Parameters
        ----------
        item : Wallet
            Item to add to the container.

        Throws
        ------
        TypeError
            If the type of the item is not Wallet.
        """

        if isinstance(item, Wallet):
            if not self.contains_address(item.address):
                super(self.__class__, self).append(item)
        else:
            raise TypeError('Tried to add a non-Wallet instance to a WalletContainer.')



    def contains_address(self, address):
        """
        Checks whether an address is added yet or not
        =============================================

        Parameters
        ----------
        address : str
            The address to search for.

        Returns
        -------
        bool
            True if the address is found, False if not.
        """

        for wallet in self:
            if wallet.address == address:
                return True
        return False



    def get_by_detail(self, key, value):
        """
        Gets wallets by a detail
        =========================

        Parameters
        ----------
        key : str
            The name of the detail to search for.
        value : str
            The value of the detail to search for.

        Returns
        -------
        list
            List of Wallet objects that matches the search.
        """

        result = []
        for wallet in self:
            if key in wallet.keys():
                if value == wallet[key]:
                    result.append(wallet)
        return result



    def get_by_displayed_name(self, name):
        """
        Gets wallets by displayed name
        ==============================

        Parameters
        ----------
        name : str
            The name to search for.

        Returns
        -------
        list
            List of Wallet object that matches the search.

        Notes
        -----
            This method implements classic string search.
        """

        result = []
        for wallet in self:
            if name in wallet.displayed_name:
                result.append(wallet)
        return result



    def get_id_by_detail(self, key, value):
        """
        Gets IDs of wallets by a detail
        ===============================

        Parameters
        ----------
        key : str
            The name of the detail to search for.
        value : str
            The value of the detail to search for.

        Returns
        -------
        list
            List of IDs of the Wallet objects that matches the search.
        """

        result = []
        for idx, wallet in enumerate(self):
            if key in wallet.keys():
                if value == wallet[key]:
                    result.append(idx)
        return result



    def get_id_by_displayed_name(self, name):
        """
        Gets IDs of wallets by displayed name
        =====================================

        Parameters
        ----------
        name : str
            The name to search for.

        Returns
        -------
        list
            List of IDs of the Wallet objects that matches the search.

        Notes
        -----
            This method implements classic string search.
        """

        result = []
        for idx, wallet in enumerate(self):
            if name in wallet.displayed_name:
                result.append(idx)
        return result



class CBTransaction(object):
    """
    This class represents a transaction
    """



    def __init__(self, tx, block_height, transaction_time, block_time,
                 first_seen_time, confirmations, inputs, outputs, fees,
                 foreign_address, confirmation_limit=6, raw=None):
        """
        Intializes the CBTransaction object
        ===================================

        Parameters
        ----------
        tx : str
            Transaction's tx ID.
        block_height : int
            The hieght of the transaction's block.
        transaction_time : int
            Transaction's time.
        block_time : int
            Time of the block of the transaction.
        first_seen_time : int
            First seen time of the transaction.
        confirmations : int
            Number of confirmations.
        inputs : list, int
            List of inputs. If set as a solo number, it gets converted into list.
        outputs : list, int
            List of outputs. If set as a solo number, it gets converted into list.
        fees : list, int
            List of fees. If set as a solo number, it gets converted into list.
        foreign_address : str
            Foreign address affected in the transaction.
        confirmation_limit : int, optional (6 if omitted)
            Confirmation limit to decide whether the transaction is well
            confirmed or not.
        raw : dict, optional (None if omitted)
            Data of the rae transaction record given by the blockchain explorer.

        Attributes
        ----------
        balance
        block_height
        block_time
        confirmations
        confirmation_limit
        fee
        fees
        first_seen_time
        inputs
        is_confirmed
        is_incoming
        is_outgoing
        is_well_confirmed
        is_unconfirmed
        Outputs
        paid
        raw
        received
        total_input
        total_output
        transaction_time
        tx
        """

        self.__tx = tx
        self.__block_height = block_height
        self.__transaction_time = transaction_timestamp
        self.__block_time = block_timestamp
        self.__first_seen_time = first_seen_time
        self.__confirmations = confirmations
        if isinstance(inputs, Iterable):
            self.__inputs = inputs
        else:
            self.__inputs = [inputs]
        if isinstance(outputs, Iterable):
            self.__outputs = outputs
        else:
            self.__outputs = [outputs]
        if isinstance(fees, Iterable):
            self.__fees = fees
        else:
            self.__fees = [fees]
        self.__foreign_address = foreign_address
        self.__confirmation_limit = 6
        self.__raw = raw

        self.__total_input = 0
        for item in inputs:
            self.__total_input += item
        self.__total_input = round(self.__total_input, 8)
        self.__total_output = 0
        for item in outputs:
            self.__total_output += item
        self.__total_output = round(self.__total_output, 8)
        self.__total_fee = 0
        for item in fees:
            self.__total_fee += item
        self.__total_fee = round(self.__total_fee, 8)
        if self.__total_input > self.__total_output:
            self.__paid = round(self.__total_input - self.__total_output, 8)
            self.__received = 0
            self.__fee = self.__total_fee
            self.__is_outgoing = True
            self.__is_incoming = False
            self.__balance = round(- self.__paid, 8)
        elif self.__total_input < self.__total_output:
            self.__paid = 0
            self.__received = round(self.__total_output - self.__total_input, 8)
            self.__fee = 0
            self.__is_outgoing = False
            self.__is_incoming = True
            self.__balance = self.__received
        else:
            self.__paid = 0
            self.__received = 0
            self.__fee = 0
            self.__is_outgoing = False
            self.__is_incoming = False
            self.__balance = 0.0



    @property
    def balance(self):
        """
        Gets the balance of the transaction
        ===================================

        Returns
        -------
        float
            The calculated baalnce.
        """

        return self.__balance



    @property
    def block_height(self):
        """
        Gets the block height of the transaction
        ========================================

        Returns
        -------
        int
            The block height.
        """

        return self.__block_height



    @property
    def block_time(self):
        """
        Gets the block time of the transaction
        ======================================

        Returns
        -------
        int
            The block time.
        """

        return self.__block_time



    @property
    def confirmations(self):
        """
        Gets the number of confirmations of the transaction
        ===================================================

        Returns
        -------
        int
            The number of confirmations.
        """

        return self.__confirmations



    @property
    def confirmation_limit(self):
        """
        Gets the value of the confirmation limit
        ========================================

        Returns
        -------
        int
            The limit to be considered as well confirmed transaction.
        """

        return self.__confirmation_limit



    @confirmation_limit.setter
    def confirmation_limit(self, newlimit):
        """
        Sets the value of the confirmation limit
        ========================================

        Parameters
        ----------
        newlimit : int
            The limit to be considered as well confirmed transaction.
        """

        self.__confirmation_limit = newlimit



    @property
    def fee(self):
        """
        Gets the fee of the transaction
        ===============================

        Returns
        -------
        float
            The calculated fee.
        """

        return self.__fee



    @property
    def fees(self):
        """
        Gets the fee components of the transaction
        ==========================================

        Returns
        -------
        list
            List of the fee components.
        """

        return self.__fees



    @property
    def first_seen_time(self):
        """
        Gets the first seen time of the transaction
        ===========================================

        Returns
        -------
        int
            The first seen time.
        """

        return self.__first_seen_time



    @property
    def inputs(self):
        """
        Gets the input components of the transaction
        ============================================

        Returns
        -------
        list
            List of the input components.
        """

        return self.__inputs



    @property
    def is_confirmed(self):
        """
        Gets whether the transaction is confirmed or not
        ==============//================================

        Returns
        -------
        bool
            True if the transaction is confirmed, False if not.
        """

        return self.confirmations > 0



    @property
    def is_incoming(self):
        """
        Gets whether the transaction is incoming or not
        ===============================================

        Returns
        -------
        bool
            True if the transaction is incoming, False if not.
        """

        return self.__is_incoming



    @property
    def is_outgoing(self):
        """
        Gets whether the transaction is outgoing or not
        ===============================================

        Returns
        -------
        bool
            True if the transaction is outgoing, False if not.
        """

        return self.__is_outgoing



    @property
    def is_well_confirmed(self):
        """
        Gets whether the transaction is well confirmed or not
        =====================================================

        Returns
        -------
        bool
            True if the transaction is well confirmed, False if not.
        """

        return self.confirmations >= self.confirmation_limit



    @property
    def is_unconfirmed(self):
        """
        Gets whether the transaction is unconfirmed or not
        ==================================================

        Returns
        -------
        bool
            True if the transaction is unconfirmed, False if not.
        """

        return self.confirmations == 0



    @property
    def outputs(self):
        """
        Gets the output components of the transaction
        ==============//=============================

        Returns
        -------
        list
            List of the output components.
        """

        return self.__outputs



    @property
    def paid(self):
        """
        Gets the paid amount of the transaction
        =======================================

        Returns
        -------
        float
            The calculated paid amount.
        """

        return self.__paid



    @property
    def raw(self):
        """
        Gets the raw data of the transaction
        ====================================

        Returns
        -------
        dict
            The raw transaction data.
        """

        return self.__raw



    @property
    def received(self):
        """
        Gets the received amount of the transaction
        ===========================================

        Returns
        -------
        float
            The calculated received amount.
        """

        return self.__received



    @property
    def total_input(self):
        """
        Gets the total input of the transaction
        =======================================

        Returns
        -------
        float
            The calculated total input.
        """

        return self.__total_input



    @property
    def total_output(self):
        """
        Gets the total output of the transaction
        ========================================

        Returns
        -------
        float
            The calculated total output.
        """

        return self.__total_output



    @property
    def transaction_time(self):
        """
        Gets the time of the transaction
        ================================

        Returns
        -------
        int
            The transaction's time.
        """

        return self.__transaction_time



    @property
    def tx(self):
        """
        Gets the tx ID of the transaction
        =================================

        Returns
        -------
        int
            The tx ID.
        """

        return self.__tx



class TransactionContainer(list):
    """
    Provides a container for the transactions of the user
    """



    def __init__(self, transactions=None):
        """
        Intializes the TransactionContainer object
        ==========================================

        Parameters
        ----------
        transactions : list
            List of transactions to add to the container right at instantiation.

        Notes
        -----
            TransactionContainer is a subclass of list, please keep this in
            mind if you are using an instance of this class.
        """

        add_transactions = True
        if transactions is None:
            add_transactions = False
        elif isinstance(transactions, Iterable):
            for transaction in transactions:
                if not isinstance(transaction, CBTransaction):
                    add_transactions = False
                    break
        if add_transactions:
            super(self.__class__, self).__init__(transactions)
        else:
            super(self.__class__, self).__init__()



    def append(self, item):
        """
        Appends a new item to the TransactionContainer
        ==============================================

        Parameters
        ----------
        item : CBTransaction
            Item to add to the container.

        Throws
        ------
        TypeError
            If the type of the item is not CBTransaction.
        """

        if isinstance(item, CBTransaction):
            if not self.contains_tx(item.tx):
                super(self.__class__, self).append(item)
        else:
            raise TypeError('Tried to add a non-CBTransaction instance to a TransactionContainer.')



    def contains_tx(self, tx):
        """
        Checks whether a tx is added yet or not
        =======================================

        Parameters
        ----------
        tx : str
            The tx to search for.

        Returns
        -------
        bool
            True if the tx is found, False if not.
        """

        for transaction in self:
            if transaction.tx == tx:
                return True
        return False



    def append_(self, item):
        """
        Appends item to the container without check
        ===========================================

        Parameters
        ----------
        item : CBTransaction
            Item to add to the container.

        Notes
        -----
            This function is a backdoor only. Its usage is unadvised and can
            lead to unexpected errors.
        """

        super(self.__class__, self).append(item)



class CBUtxo(object):
    """
    This class represents an utxo
    """

    def __init__(self, tx, amount, sat_amount, block_height, confirmations):
        """
        Initializes the CBUtxo object
        =============================

        Parameters
        ----------
        tx : int
            Tx ID of the utxo.
        amount : float
            The amount of the utxo in bitcoincash.
        sat_amount : int
            The amount of the utxo in satoshis.
        block_height : int
            The block height of the utxo.
        confirmations : int
            The number of confirmations of the utxo.
        """

        self.__tx = tx
        self.__amount = amount
        self.__sat_amount = sat_amount
        self.__block_height = block_height
        self.__confirmations = confirmations



    @property
    def amount(self):
        """
        Gets the amount stored in the utxo
        ==================================

        Returns
        -------
        float
            The amount stored.
        """

        return self.__amount



    @property
    def block_height(self):
        """
        Gets the block height of the utxo
        =================================

        Returns
        -------
        int
            The block height.
        """

        return self.__block_height



    @property
    def confirmations(self):
        """
        Gets the number of confirmations of the utxo
        ============================================

        Returns
        -------
        int
            The number of confirmations.
        """

        return self.__confirmations



    @property
    def sat_amount(self):
        """
        Gets the satoshis stored in the utxo
        ====================================

        Returns
        -------
        int
            The amount stored.
        """

        return self.__sat_amount



    @property
    def tx(self):
        """
        Gets the tx ID of the utxo
        ==========================

        Returns
        -------
        int
            The tx ID.
        """

        return self.__tx




class UtxoContainer(list):
    """
    Provides a container for the utxos of the user

    Notes
    -----
        Both utxos and uncofrimed utxos are stored in the same container types.
        Though the container types are the same, this means two separate
        instances.
    """



    def __init__(self, utxos=None):
        """
        Intializes the UtxoContainer object
        ===================================

        Parameters
        ----------
        utxos : list
            List of utxos to add to the container right at instantiation.

        Notes
        -----
            UtxoContainer is a subclass of list, please keep this in mind if
            you are using an instance of this class.
        """

        add_utxos = True
        if utxos is None:
            add_utxos = False
        elif isinstance(utxos, Iterable):
            for utxo in utxos:
                if not isinstance(utxo, CBUtxo):
                    add_utxos = False
                    break
        if add_utxos:
            super(self.__class__, self).__init__(utxos)
        else:
            super(self.__class__, self).__init__()



    def append(self, item):
        """
        Appends a new item to the UtxoContainer
        =======================================

        Parameters
        ----------
        item : CBUtxo
            Item to add to the container.

        Throws
        ------
        TypeError
            If the type of the item is not CBUtxo.
        """

        if isinstance(item, CBUtxo):
            if not self.contains_tx(item.tx):
                super(self.__class__, self).append(item)
        else:
            raise TypeError('Tried to add a non-CBUtxo instance to a UtxoContainer.')



    def contains_tx(self, tx):
        """
        Checks whether a tx is added yet or not
        =======================================

        Parameters
        ----------
        tx : str
            The tx to search for.

        Returns
        -------
        bool
            True if the tx is found, False if not.
        """

        for utxo in self:
            if utxo.tx == tx:
                return True
        return False



    def append_(self, item):
        """
        Appends item to the container without check
        ===========================================

        Parameters
        ----------
        item : CBUtxo
            Item to add to the container.

        Notes
        -----
            This function is a backdoor only. Its usage is unadvised and can
            lead to unexpected errors.
        """

        super(self.__class__, self).append(item)



class CBDocument(object):
    """
    This class represents the top level parent class of documents
    """



    DOCUMENT_INSTANTIATED = 0
    DOCUMENT_CREATED = 1
    DOCUMENT_HAS_ID = 2
    DOCUMENT_CLOSED = 4
    DOCUMENT_EXPIRES = 8
    DOCUMENT_IS_ANONYMOUS = 16
    DOCUMENT_IS_CERTIFIED = 32
    DOCUMENT_EXPIRED = 64



    def __init__(self, owner=None, id=None, created_at=None, closed_at=None,
                 expires_at=None, is_certified=False, is_anonymous=False):

        self.__owner = None
        self.__id = None
        self.__created = None
        self.__closed = None
        self.__expires = None
        self.__certified = False
        self.__anonymous = False
        self.owner = owner
        self.id = id
        self.created = created_at
        self.closed = closed_at
        self.expires = expires_at
        self.certified = is_certified



    @property
    def anonymous(self):

        return self.__anonymous



    @anonymous.setter
    def anonymous(self, newstate):

            self.__anonymous = newstate



    @property
    def certified(self):

        return self.__certified



    @certified.setter
    def certified(self, newstate):

        self.__certified = newstate



    @property
    def closed(self):

        return self.__closed



    @closed.setter
    def closed(self, timestamp=0):

        if self.__closed is None:
            if timestamp == 0:
                self.__closed = now()
            else:
                if timestamp <= now():
                    self.__closed = timestamp
                else:
                    raise ValueError('ChainBridgeDocument can be just closed now or can be restored.')
        else:
            raise PermissionError('Tried to close a closed ChainBridgeDocument instance.')



    @property
    def created(self):

        return self.__created



    @created.setter
    def created(self, timestamp=0):

        if self.__created is None:
            if timestamp == 0:
                self.__created = now()
            else:
                if timestamp <= now():
                    self.__created = timestamp
                else:
                    raise ValueError('ChainBridgeDocument can be just created now or can be restored.')
        else:
            raise PermissionError('Tried to create a created ChainBridgeDocument instance.')



    @property
    def expires(self):

        return self.__expires



    @expires.setter
    def expires(self, timestamp):

        if self.is_editable_('set expieration'):
            self.__expires = timestamp



    @property
    def id(self):

        return self.__id



    @id.setter
    def id(self, newid):

        if self.is_editable_('add id'):
            if self.__id is None:
                self.__id = newid
            else:
                raise PermissionError('Tried to add id for a ChainBridgeDocument instance with id.')



    @property
    def owner(self):

        return self.__owner



    @owner.setter
    def owner(self, newowner):

        if self.is_editable_('add owner'):
            if self.__owner is None:
                self.__owner = newowner
            else:
                raise PermissionError('Tried to add owner for a ChainBridgeDocument instance with owner.')



    @property
    def state(self):

        result = CBDocument.DOCUMENT_INSTANTIATED
        if self.created is not None:
            result += CBDocument.DOCUMENT_CREATED
        if self.id is not None:
            result += CBDocument.DOCUMENT_HAS_ID
        if self.closed is not None:
            result += CBDocument.DOCUMENT_CLOSED
        if self.expires is not None:
            result += CBDocument.DOCUMENT_EXPIRES
        if self.anonymous:
            result += CBDocument.DOCUMENT_IS_ANONYMOUS
        if self.certified:
            result += CBDocument.DOCUMENT_IS_CERTIFIED
        if self.expires < now():
            result += CBDocument.DOCUMENT_EXPIRED
        return result



    def is_editable_(self, activity_name='manipulate', drop_error=True):

        if self.created is None or self.closed is not None:
            if drop_error:
                raise PermissionError('Tried to {} of a ChainBridgeDocument instance in non-editable state.'
                                      .format(activity_name))
            else:
                return False
        else:
            return True;



class ProtectedCBDocument(CBDocument):
    """
    This is an abstract mid-level class to relize a protected document
    ==================================================================
    """



    def __init__(self, owner, permission_function, id=None,
                 created_at=None, closed_at=None, expires_at=None,
                 is_certified=False, is_anonymous=False):

        super(self.__class__, self).__init__(owner=owner, id=id,
                                             created_at=created_at,
                                             closed_at=closed_at,
                                             expires_at=expires_at,
                                             is_certified=is_certified,
                                             is_anonymous=is_anonymous)
        self.__check_permission = permission_function



    @CBDocument.anonymous.setter
    def anonymous(self, newstate):

        if self.check_permission('anonymous'):
            super(self.__class__, self).anonymous(newstate)



    @property
    def check_permission(self, query_string):

        return self.__check_permission(query_string)



    @CBDocument.certified.setter
    def certified(self, newstate):

        if self.check_permission('certify'):
            super(self.__class__, self).certified(newstate)



class StatementOfAccount(ProtectedCBDocument):
    """
    This class represents an Account Activity document
    """



    def __init__(self, owner, from_date, to_date, permission_function, id=None,
                 created_at=None, closed_at=None, expires_at=None,
                 is_certified=False, is_anonymous=False):

        if created_at is None:
            created_at = now()
        super(self.__class__, self).__init__(owner=owner,
                                             permission_function=permission_function,
                                             id=id, created_at=created_at,
                                             closed_at=closed_at,
                                             expires_at=expires_at,
                                             is_certified=is_certified,
                                             is_anonymous=is_anonymous)
        if from_date > now():
            raise ValueError('StatementOfAccount.init() - beginning cannot be in the future.')
        if to_date < from_date:
            raise ValueError('StatementOfAccount.init() - ending date cannot be earlier than beginning date.')
        self.__from_date = from_date
        self.__to_date = to_date



    @property
    def from_date(self):

        return self.__from_date



    @property
    def to_date(self):

        return self.__to_date



class AccountActivity(ProtectedCBDocument):
    """
    This class represents an Account Activity document
    """



    def __init__(self, owner, search, permission_function, id=None,
                 created_at=None, closed_at=None, expires_at=None,
                 is_certified=False, is_anonymous=False):

        if created_at is None:
            created_at = now()
        super(self.__class__, self).__init__(owner=owner,
                                             permission_function=permission_function,
                                             id=id, created_at=created_at,
                                             closed_at=closed_at,
                                             expires_at=expires_at,
                                             is_certified=is_certified,
                                             is_anonymous=is_anonymous)
        self.__search = search



    @property
    def search(self):

        return self.__search



class SearchObject(object):
    """
    This class contains a search of a user
    ======================================
    """



    def __init__(self, filters):

        self.__filter_list = []
        for filter in filters:
            pass


    def add_filter(self, filter_type, filter_value):

        pass



    def apply_filter(self, transactions):

        pass



    def change_filter(self, filter_type, filter_value):

        result = []
        match = False
        for _filter in self.__filter_list:
            if _filter[0] == filter_type:
                match = True
            else:
                if SearchObject.is_valid_(filter_type, filter_value)
                    result.append(_filter)
                else:
                    raise ValueError('Tried to change to non-valid filter.')
        if match:
            self.__filter_list = result
        else:
            raise ValueError('Cannot change non-existing filter-type.')



    @property
    def filter_list(self):

        result = []
        for _filter in self.__filter_list:
            result.append(_filter)
        return result



    def get_filter(self, id):

        return self.__filter_list[id]



    def remove_filter_by_id(self, id):

        if id < len(self.__filter_list) and id >= 0:
            result = []
            for i in range(len(self.__filter_list)):
                if i != id:
                    result.append(self.__filter_list[i])
            self.__filter_list = result
        else:
            raise ValueError('Cannot remove non-existing id.')



    def remove_filter_by_type(self, filter_type):

        result = []
        match = False
        for _filter in self.__filter_list:
            if _filter[0] == filter_type:
                match = True
            else:
                result.append(_filter)
        if match:
            self.__filter_list = result
        else:
            raise ValueError('Cannot remove non-existing filter-type.')



    @classmethod
    def is_valid_(cls, filter_type, filter_value):

        return True



def bch_2_sat(bch):
    """
    Converts bitcoincash amount to satoshi
    ======================================

    Parameters
    ----------
    bch : float
        The value to convert.

    Returns
    -------
    int
        The converted satoshi value.
    """

    return int(round(bch * 100000000))



def generic_permission_function(query_string):
    """
    Permission function template
    ============================

    Parameters
    ----------
    query_string : str
        The name of the activity (modification metchod) to decide whether to
        allow or not.

    Returns
    -------
    bool
        This function always returns True.

    Notes
    -----
        As long as the software is in development state it seems to be a good
        practice to have a very permissive function for testing purposes.
    """

    return True



def generic_permission_function_for_restore(query_string):
    """
    Permission function template for restoring instances
    ====================================================

    Parameters
    ----------
    query_string : str
        The name of the activity (modification metchod) to decide whether to
        allow or not.

    Returns
    -------
    bool
        This function always returns False.

    Notes
    -----
        In case of restoring an object eg. from file it seems to be a good
        practice don't let the user/developer to make modifications. Moreover in
        case of a certified document this habit is a must.
    """

    return False



def has_state(status_code, target_code):
    """
    Gets whether a composed state variable contains a specific state or not
    =======================================================================

    Params
    ------
    status_code : int
        The composed code, which potentially consists multiple status flags.
    target_code : int
        The status code identifier which is serached.

    Returns
    -------
    bool
        True if target_code is part of status_code, False if not.

    Notes
    -----
        This function works with binary flags only.
    """

    return status_code // target_code % 2 == 1



def is_equal_bch(one, another):
    """
    Compares two numbers whether they are equal or not
    ==================================================

    Parameters
    ----------
    one : float
        One number to compare.
    another : float
        Another number to compare.

    Returns
    -------
    bool
        True if the two numbers seem to be equal or False of not.

    Notes
    -----
        By working with floating point numbers especially in case of bitcoincash
        - where calculating with 8 decimal precision is a must - developers face
        the problem of precision quite often due to the lack of the perfect
        precision with floating points. To avoid it the use of satoshis or the
        use of Decimal are both good solutions but sometimes old approximation
        solutions, like this function should applied too.
    """

    return round(abs(one - another), 8) == 0



def now():
    """
    Gets the actual timestamp
    =========================

    Returns
    -------
    int
        Second based timesampt.
    """

    return int(time())



def sat_2_bch(satoshi):
    """
    Converts satoshi to bitcoincash amount
    ======================================

    Parameters
    ----------
    satoshi : int
        The value to convert.

    Returns
    -------
    float
        The converted bitcoincash value.
    """

    return round(satoshi / 100000000, 8)

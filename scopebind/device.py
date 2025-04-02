import os
import ctypes
import queue
import time
import threading


class Device:
    """
        Supported & Tested Devices:
            Instrustar ISDS205X
            - YiXingDianZi, Harbin Instrument Star Electronic Technology Co., Ltd.
            - USB Substring: "USB\\VID_D4A2&PID_5661"
            - Initial version based on https://github.com/instrustar-dev/SDK/tree/master
    """
    def __init__(self, vendor_id: int = 0xD4A2, product_id: int = 0x5661):
        """
        Initialize the device with Vendor ID and Product ID.

        :param vendor_id: USB Vendor ID of the device
        :param product_id: USB Product ID of the device
        """
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = None

        # Load DLL
        dir_path = os.path.dirname(os.path.realpath(__file__))
        os.add_dll_directory(os.path.join(dir_path, "SharedLibrary/Windows/X64/Release"))

        # Initialize the data queue
        self.data_queue = queue.Queue()
        self.data_queue_lock = threading.Lock()  # Create a lock to protect the shared resource

    def start(self):
        """
        Connect to the USB oscilloscope device.
        """

        ## Load library __stdcall using  windll
        mdll = ctypes.WinDLL("VDSO.dll")

        ############################ Initialization/Finished Dll ##############################
        ## init Dll
        fInitDll = mdll.InitDll
        fInitDll.restype = ctypes.c_int
        ## finish Dll
        fFinishDll = mdll.FinishDll
        fFinishDll.restype = ctypes.c_int

        ########################### Device ##############################
        ## get equipment information id0
        fGetOnlyId0 = mdll.GetOnlyId0
        fGetOnlyId0.restype = ctypes.c_uint
        ## get equipment information id1
        fGetOnlyId1 = mdll.GetOnlyId1
        fGetOnlyId1.restype = ctypes.c_uint
        ## reset device
        fResetDevice = mdll.ResetDevice
        fResetDevice.restype = ctypes.c_int

        ############################ USB status ##############################
        fSetDevNoticeCallBack = mdll.SetDevNoticeCallBack
        # fSetDevNoticeCallBack.restype = ctypes.void
        ## check instrument connection
        fIsDevAvailable = mdll.IsDevAvailable
        fIsDevAvailable.restype = ctypes.c_int

        ############################ Oscilloscope ##############################
        ## capture range set
        fSetOscChannelRange = mdll.SetOscChannelRange
        fSetOscChannelRange.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        fSetOscChannelRange.restype = ctypes.c_int
        ## get coupling mode
        fGetAcDc = mdll.GetAcDc
        fGetAcDc.argtypes = [ctypes.c_uint]
        fGetAcDc.restype = ctypes.c_int
        ## get sample num
        fGetOscSupportSampleNum = mdll.GetOscSupportSampleNum
        fGetOscSupportSampleNum.restype = ctypes.c_int
        ## get support sample num
        fGetOscSupportSamples = mdll.GetOscSupportSamples
        fGetOscSupportSamples.restype = ctypes.c_int
        ## set sample
        fSetOscSupportSamples = mdll.SetOscSample
        fSetOscSupportSamples.restype = ctypes.c_uint

        ############################ Capture ##############################
        ## get Memory Length
        fGetMemoryLength = mdll.GetMemoryLength
        fGetMemoryLength.restype = ctypes.c_uint
        ## Capture
        fCapture = mdll.Capture
        fCapture.restype = ctypes.c_int

        ############################ Data Ready ##############################
        fSetDataReadyCallBack = mdll.SetDataReadyCallBack

        ############################ Read Data ##############################
        fReadVoltageDatas = mdll.ReadVoltageDatas
        fReadVoltageDatas.restype = ctypes.c_uint

        ## init Dll
        print('## Init Dll: ', fInitDll())

        ##Data Revice
        @ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p)
        def DevDataReadyCallBack_func(p):
            print('## DevDataReadyCallBack_func', p)

            totallength = fGetMemoryLength() * 1024;
            print('total length:', totallength)
            arraytypedouble = ctypes.c_double * totallength
            datas = arraytypedouble()
            num = fReadVoltageDatas(ctypes.c_char(0), datas, totallength);
            minv = datas[0];
            maxv = datas[0];
            for index in range(num):
                if (datas[index] < minv):
                    minv = datas[index];
                if (datas[index] > maxv):
                    maxv = datas[index];
            print('## fReadVoltageDatas', num)
            print(' minv', minv)
            print(' maxv', maxv)

            with self.data_queue_lock:
                for item in datas:
                    self.data_queue.put(item)

            # Next Capture
            length = fGetMemoryLength();
            fCapture(length);
            return 0

        ##USB status
        @ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p)
        def DevNoticeAddCallBack_func(p):
            print('DevNoticeAddCallBack_func', p)

            ## test not used
            while not fIsDevAvailable():
                print("Not yet available, re-plug USB oscilloscope")
                time.sleep(1.0)
                fResetDevice()
            print('## connection ok:', fIsDevAvailable())

            ## onyid
            print('## ID0: ', fGetOnlyId0())
            print('## ID1: ', fGetOnlyId1())

            ## acdc
            print('## ch0 coupling type ', fGetAcDc(0))
            print('## ch1 coupling type ', fGetAcDc(1))

            ## set range to +/- 5000mV
            print('## ch0 range set: ', fSetOscChannelRange(0, -6000, 6000))
            print('## ch1 range set: ', fSetOscChannelRange(1, -6000, 6000))

            ## Sample
            samplenum = fGetOscSupportSampleNum()
            print('## support sample number: ', samplenum)
            arraytype = ctypes.c_uint * samplenum
            samples = arraytype()
            fGetOscSupportSamples(samples, samplenum)
            print("samples size options")
            for s in samples:
                print(s)

            # fSetOscSupportSamples(samples[samplenum-1]); # highest sampling rate
            # fSetOscSupportSamples(samples[0])  # lowest sampling rate
            fSetOscSupportSamples(4000000)

            length = fGetMemoryLength()
            print('## MemoryLength ', length * 1024)

            para = ctypes.c_void_p(p+1)
            fSetDataReadyCallBack(para, DevDataReadyCallBack_func)
            fCapture(length)

            return 0

        @ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p)
        def DevNoticeRemoveCallBack_func(p):
            print('## DevNoticeRemoveCallBack_func', p)
            ## finish Dll
            print('## Finish Dll: ', fFinishDll())
            return 0

        # 1000 is just test
        para = ctypes.c_void_p(1)
        # fSetDevNoticeCallBack(para, DevNoticeAddCallBack_func, DevNoticeRemoveCallBack_func)

        # store callback function references
        self.DevDataReadyCallBack_func = DevDataReadyCallBack_func
        self.DevNoticeAddCallBack_func = DevNoticeAddCallBack_func
        self.DevNoticeRemoveCallBack_func = DevNoticeRemoveCallBack_func

        self.DevNoticeAddCallBack_func(para)

        # while True:
        #     pass

    def read(self, size: int = 64) -> bytes:
        """
        Read data from the oscilloscope device.

        :param size: Number of bytes to read
        :return: Data read from the device
        """
        data = []
        while len(data) < size:
            with self.data_queue_lock:
                try:
                    item = self.data_queue.get(block=False)
                    data.append(item)
                except:
                    pass
        return data


    def stop(self):
        self.DevNoticeRemoveCallBack_func(1)

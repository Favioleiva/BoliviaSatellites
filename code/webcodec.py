"""Lossless byte shuffle for Float64 gzip; no quantisation or float conversion."""
import gzip,struct
import numpy as np
MAGIC=b'C05SHF01'
def encode(array,shuffled=False):
    a=np.asarray(array,dtype='<f8');raw=a.tobytes(order='C')
    if shuffled:
        rows,cols=(a.shape if a.ndim==2 else (len(a),1));raw=a.tobytes(order='F')
        raw=b'C05SHF02'+struct.pack('<II',rows,cols)+np.frombuffer(raw,dtype=np.uint8).reshape(-1,8).T.copy().tobytes()
    return gzip.compress(raw,compresslevel=6,mtime=0)
def decode(blob):
    raw=gzip.decompress(blob)
    if raw.startswith(b'C05SHF02'):
        rows,cols=struct.unpack('<II',raw[8:16]);raw=np.frombuffer(raw[16:],dtype=np.uint8).reshape(8,-1).T.copy().tobytes()
        return np.frombuffer(raw,dtype='<f8').reshape(rows,cols,order='F').ravel(order='C')
    if raw.startswith(MAGIC):raw=np.frombuffer(raw[8:],dtype=np.uint8).reshape(8,-1).T.copy().tobytes()
    return np.frombuffer(raw,dtype='<f8')

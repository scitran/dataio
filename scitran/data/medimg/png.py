# @author:  Gunnar Schaefer
#           Kevin S Hahn

"""
nimsdata.medimg.png
===================

PNG provides PNG image writing capabilities for medimg datasets.

"""

import os
import logging
from PIL import Image

import numpy as np

import medimg

log = logging.getLogger(__name__)


class PNGError(medimg.MedImgError):
    pass


class PNG(medimg.MedImgWriter):

    datakind = u'derived'
    datatype = u'bitmap'
    filetype = u'png'

    @classmethod
    def write(cls, metadata, imagedata, outbase, voxel_order=None):
        """
        Create png files for each image in a list of pixel data.

        Parameters
        ----------
        metadata : object
            fully loaded instance of a NIMSReader.
        imagedata : dict
            dictionary of np.darrays. label suffix as keys, with np.darrays as values.
        outbase : str
            output name prefix.
        voxel_order : str [default None]
            three character string indicating the voxel order, ex. 'LPS'.

        Returns
        -------
        results : list
            list of files written.

        Raises
        ------
        NIMSDataError
            metadata or data is None.

        """
        super(PNG, cls).write(metadata, imagedata, outbase, voxel_order)  # XXX FAIL! unexpected imagedata = None
        results = []
        for data_label, data in imagedata.iteritems():
            if data is None:
                continue
            if voxel_order and metadata.qto_xyz:  # cannot reorder if no affine
                data, qto_xyz = cls.reorder_voxels(data, metadata.qto_xyz, voxel_order)
            else:
                qto_xyz = metadata.qto_xyz
            outname = outbase + data_label
            data = np.dsplit(data, len(metadata._dcm_list))  # cut the darray
            data = [image.squeeze() for image in data]  # squeeze; remove axis with 1 val
            for i, data in enumerate(data):
                filepath = outname + '_%d' % (i + 1) + '.png'
                if data.ndim == 2:
                    data = data.astype(np.int32)
                    data = data.clip(0, (data * (data != (2**15 - 1))).max())  # -32768->0; 32767->brain.max
                    data = data * (2**8 - 1) / data.max()  # scale to full 8-bit range
                    Image.fromarray(data.astype(np.uint8), 'L').save(filepath, optimize=True)
                elif data.ndim == 3:
                    data = data.reshape((data.shape[1], data.shape[2], data.shape[0]))
                    Image.fromarray(data, 'RGB').save(filepath, optimize=True)
                log.debug('generated %s' % os.path.basename(filepath))
                results.append(filepath)
            log.debug('returning:  %s' % filepath)
        return results

write = PNG.write

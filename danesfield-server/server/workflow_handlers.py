#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
##############################################################################

import re

from girder.models.item import Item

from . import algorithms
from .constants import DanesfieldStep
from .workflow import DanesfieldWorkflowException


def _fileFromItem(item):
    """
    Return the file contained in an item. Raise an exeception if the item doesn't contain
    exactly one file.
    """
    files = Item().childFiles(item, limit=2)
    if files.count() != 1:
        raise DanesfieldWorkflowException(
            'Item must contain %d files, but should contain only one.' % files.count())
    return files[0]


def _removeDuplicateCount(name):
    """
    Remove duplicate count suffix from a name.
    For example, 'my_file (1).txt' becomes 'my_file.txt'.
    """
    return re.sub(r' \(\d+\)$', '', name)


def _isPointCloud(item):
    """
    Return true if the item refers to a point cloud.

    :param item: Item document.
    :type item: dict
    """
    return _removeDuplicateCount(item['name']).lower().endswith('.las')


def _isMsiImage(item):
    """
    Return true if the item refers to an MSI image.

    :param item: Item document.
    :type item: dict
    """
    return '-m' in item['name'].lower()


def _isPanImage(item):
    """
    Return true if the item refers to a PAN image.

    :param item: Item document.
    :type item: dict
    """
    return '-p' in item['name'].lower()


def _getWorkingSet(name, workingSets):
    """
    Get a specific working set by name. Raise an error if the working set is not found.

    :param name: The name of the working set.
    :type name: str
    :param workingSets: The available working sets.
    :type workingSets: dict
    """
    workingSet = workingSets.get(name)
    if workingSet is None:
        raise DanesfieldWorkflowException('Error looking up working set \'{}\''.format(name))
    return workingSet


def runGeneratePointCloud(requestInfo, jobId, workingSets, outputFolder, options):
    """
    Workflow handler to run p3d to generate a point cloud.

    Supports the following options:
    - longitude (required)
    - latitude (required)
    - longitudeWidth (required)
    - latitudeWidth (required)
    """
    # Get working set
    workingSet = _getWorkingSet(DanesfieldStep.INIT, workingSets)

    # Get IDs of PAN image files
    items = [Item().load(itemId, force=True, exc=True) for itemId in workingSet['datasetIds']]
    panItems = [item for item in items if _isPanImage(item)]
    panFileIds = [_fileFromItem(item)['_id'] for item in panItems]

    # Get required options
    generatePointCloudOptions = options.get(DanesfieldStep.GENERATE_POINT_CLOUD)
    if generatePointCloudOptions is None or not isinstance(generatePointCloudOptions, dict):
        raise DanesfieldWorkflowException('Invalid options provided for step: {}'.format(
            DanesfieldStep.GENERATE_POINT_CLOUD
        ))

    try:
        longitude = generatePointCloudOptions['longitude']
        latitude = generatePointCloudOptions['latitude']
        longitudeWidth = generatePointCloudOptions['longitudeWidth']
        latitudeWidth = generatePointCloudOptions['latitudeWidth']
    except KeyError:
        raise DanesfieldWorkflowException(
            'The {} step requires the following options: longtitude, latitude, longitudewith, '
            'latitudeWidth'.format(DanesfieldStep.GENERATE_POINT_CLOUD))

    # Run algorithm
    algorithms.generatePointCloud(
        requestInfo=requestInfo, jobId=jobId, trigger=True,
        imageFileIds=panFileIds, outputFolder=outputFolder,
        longitude=longitude, latitude=latitude,
        longitudeWidth=longitudeWidth, latitudeWidth=latitudeWidth)


def runGenerateDsm(requestInfo, jobId, workingSets, outputFolder, options):
    """
    Workflow handler to run generate_dsm.
    """
    # Get working set
    workingSet = _getWorkingSet(DanesfieldStep.GENERATE_POINT_CLOUD, workingSets)

    # Get point cloud file
    items = [Item().load(itemId, force=True, exc=True) for itemId in workingSet['datasetIds']]
    pointCloudItems = [item for item in items if _isPointCloud(item)]
    if not pointCloudItems:
        raise DanesfieldWorkflowException('Unable to find point cloud')
    if len(pointCloudItems) > 1:
        raise DanesfieldWorkflowException(
            'Expected only one point cloud, got {}'.format(len(pointCloudItems)))
    pointCloudItem = pointCloudItems[0]
    pointCloudFile = _fileFromItem(pointCloudItem)

    # Run algorithm
    algorithms.generateDsm(
        requestInfo=requestInfo, jobId=jobId, trigger=True,
        file=pointCloudFile, outputFolder=outputFolder)


def runFitDtm(requestInfo, jobId, workingSets, outputFolder, options):
    """
    Workflow handler to run fit_dtm.

    Supports the following options:
    - iterations
    - tension
    """
    # Get working set
    workingSet = _getWorkingSet(DanesfieldStep.GENERATE_DSM, workingSets)

    # Get DSM
    items = [Item().load(itemId, force=True, exc=True) for itemId in workingSet['datasetIds']]
    if not items:
        raise DanesfieldWorkflowException('Unable to find DSM')
    if len(items) > 1:
        raise DanesfieldWorkflowException('Expected only one input file, got {}'.format(len(items)))
    file = _fileFromItem(items[0])

    # Get options
    fitDtmOptions = options.get(DanesfieldStep.FIT_DTM)
    if fitDtmOptions is not None and not isinstance(fitDtmOptions, dict):
        raise DanesfieldWorkflowException('Invalid options provided for step: {}'.format(
            DanesfieldStep.FIT_DTM
        ))

    # Run algorithm
    algorithms.fitDtm(
        requestInfo=requestInfo, jobId=jobId, trigger=True, file=file,
        outputFolder=outputFolder, **fitDtmOptions)


def runFinalize(requestInfo, jobId, workingSets, outputFolder, options):
    """
    Workflow handler to run finalize step.
    """
    algorithms.finalize(requestInfo=requestInfo, jobId=jobId)

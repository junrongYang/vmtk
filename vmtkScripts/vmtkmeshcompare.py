#!/usr/bin/env python

import sys
import vtk
import vtkvmtk
import pypes

vmtkmeshcompare = 'vmtkMeshCompare'

class vmtkMeshCompare(pypes.pypeScript):

    def __init__(self):

        pypes.pypeScript.__init__(self)

        self.Mesh = None
        self.ReferenceMesh = None
        self.Method = ''
        self.ArrayName = ''
	self.Tolerance = 1E-8
        self.Result = ''
        self.ResultLog = ''
        self.ResultData = None

        self.SetScriptName('vmtkmeshcompare')
        self.SetScriptDoc('compares a  mesh against a reference')
        self.SetInputMembers([
            ['Mesh','i','vtkUnstructuredGrid',1,'','the input mesh','vmtkmeshreader'],
            ['ReferenceMesh','r','vtkUnstructuredGrid',1,'','the reference mesh to compare against','vmtkmeshreader'],
            ['Method','method','str',1,'["quality","array"]','method of the test'],
            ['ArrayName','array','str',1,'','name of the array'],
            ['Tolerance','tolerance','float',1,'','tolerance for numerical comparisons'],
            ])
        self.SetOutputMembers([
            ['Result','result','bool',1,'','Output boolean stating if meshes are equal or not'],
            ['ResultData','o','vtkUnstructuredGrid',1,'','the output mesh','vmtkmeshwriter'],
            ['ResultLog','log','str',1,'','Result Log']
            ])

    def arrayCompare(self):

        if not self.ArrayName:
            self.PrintError('Error: No ArrayName.') 
        if not self.ReferenceMesh.GetCellData().GetArray(self.ArrayName):
            self.PrintError('Error: Invalid ArrayName.')
        if not self.Mesh.GetCellData().GetArray(self.ArrayName):
            self.PrintError('Error: Invalid ArrayName.')

        referenceArrayName = 'Ref' + self.ArrayName
        meshPoints = self.Mesh.GetNumberOfPoints()
        referencePoints = self.ReferenceMesh.GetNumberOfPoints() 
        pointsDifference = meshPoints - referencePoints

        self.PrintLog("Mesh points: "+ str(meshPoints)) 
        self.PrintLog("Reference Points: " +str(referencePoints))

        if abs(pointsDifference) > 0:
            self.ResultLog = 'Uneven NumberOfPoints'
            return False

        refArray = self.ReferenceMesh.GetCellData().GetArray(self.ArrayName) 
        refArray.SetName(referenceArrayName) 
        self.Mesh.GetCellData().AddArray(refArray)

        calculator = vtk.vtkArrayCalculator() 
        calculator.SetInput(self.Mesh)
        calculator.SetAttributeModeToUseCellData()
        calculator.AddScalarVariable('a',self.ArrayName,0)
        calculator.AddScalarVariable('b',referenceArrayName,0)
        calculator.SetFunction("a - b") 
        calculator.SetResultArrayName('ResultArray')
        calculator.Update()

        self.ResultData = calculator.GetOutput()
        resultRange = self.ResultData.GetCellData().GetArray('ResultArray').GetRange()

        self.PrintLog('Result Range: ' + str(resultRange))

        if max([abs(r) for r in resultRange]) < self.Tolerance:
            return True

        return False

    def qualityCompare(self):
        
        meshQuality = vtk.vtkMeshQuality()
        meshQuality.SetInput(self.Mesh)
        meshQuality.RatioOn()
        meshQuality.Update()
        meshQualityOutput = meshQuality.GetOutput()

        referenceQuality = vtk.vtkMeshQuality()
        referenceQuality.SetInput(self.ReferenceMesh)
        referenceQuality.RatioOn()
        referenceQuality.Update()
        referenceQualityOutput = referenceQuality.GetOutput()

        self.PrintLog("Mesh points: "+ str(meshQualityOutput.GetNumberOfPoints()))
        self.PrintLog("Reference Points: " +str(referenceQualityOutput.GetNumberOfPoints()))

        meshQualityRange = meshQualityOutput.GetCellData().GetArray("Quality").GetRange()
        referenceQualityRange = referenceQualityOutput.GetCellData().GetArray("Quality").GetRange()
        qualityRangeDifference = (meshQualityRange[0] - referenceQualityRange[0],meshQualityRange[1] - referenceQualityRange[1])

  	self.PrintLog("Mesh Quality Range: "+ str(meshQualityRange))
  	self.PrintLog("Reference Quality Range: "+ str(referenceQualityRange))
  	self.PrintLog("Quality Range Difference: "+ str(qualityRangeDifference))

        if max(abs(d) for d in qualityRangeDifference) < self.Tolerance:
            return True

        return False

    def Execute(self):

        if not self.Mesh:
            self.PrintError('Error: No mesh.')
        if not self.ReferenceMesh:
            self.PrintError('Error: No reference.')
        if not self.Method:
            self.PrintError('Error: No method.')                 

        if (self.Method == 'quality'):
            self.Result = self.qualityCompare()
        elif (self.Method == 'array'):
            self.Result = self.arrayCompare()

        
if __name__=='__main__':
    main = pypes.pypeMain()
    main.Arguments = sys.argv
    main.Execute()

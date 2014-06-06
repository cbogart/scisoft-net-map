' Version 2.1, by Sadegh Mirshekarian, 3/2012
' **************************************************************************************************************

''' < Partitioning the DSM based on the reachability matrix results >
''' -----------------------------------

''' Macro originally recorded 8/17/98 by Qi Dong and modified by Ali Yassine 3/23/99


Option Explicit
Option Base 1
Dim taken, temp, c As Variant


Sub Partition()

    ReDim taken(elementNum), temp(elementNum), c(elementNum) 'taken(x)=1 means element x has already been taken out at a level
    Dim i, j, k, m, total, elevel As Integer
    Dim index, signal As Integer
    Dim passedTime As Variant
    Dim tmpComment As String
    
    Application.ScreenUpdating = False
    
    ''' preparing the sheets
    Worksheets("New Sequence").Select
    Range(Cells(1, 2), Cells(250, 250)).Select
    Selection.ClearContents
    Cells(1, 1).Select
    
    Worksheets("Partitioned DSM").Select
    Range(Cells(1, 1), Cells(250, 250)).Select
    Selection.ClearContents
    Selection.ClearComments
    Selection.Interior.ColorIndex = 2
    Cells(1, 1).Value = "PARTITIONED DSM"
    
    For i = 1 To elementNum
        Cells(i + 2, i + 2).Select
        With Selection.Interior
            .ColorIndex = 1
            .Pattern = xlSolid
        End With
    Next i
    
    ''' partitioning work starts here
    
    For i = 1 To elementNum
        taken(i) = 0
        c(i) = 1
    Next i
    
    total = elementNum
    elevel = 0
    
    Do Until total = 0
        
        elevel = elevel + 1
        For i = 1 To elementNum
            
            signal = 0
            For j = 1 To reachFromSet_num(i)
                If taken(reachFromSet(i, j)) = 0 Then
                    If reach(reachFromSet(i, j), i) <> 0 Then signal = 1 Else signal = 0
                    'signal = 1 means a cycle exists between i and reachFromSet(i , j)
                Else
                    signal = 1
                End If
                If signal = 0 Then Exit For
            Next j
        
            m = 0
            If signal = 1 Then
                For j = 1 To reachFromSet_num(i)
                    If taken(reachFromSet(i, j)) = 0 Then
                        m = m + 1
                        total = total - 1
                        temp(m) = reachFromSet(i, j)
                        taken(reachFromSet(i, j)) = 1
                    End If
                Next j
                'output to the sheet "New Sequence"
                For j = 1 To m
                    Worksheets("New Sequence").Cells(elevel, c(elevel) + j).Value = temp(j)
                Next j
                c(elevel) = c(elevel) + m
            End If
        Next i
    Loop
    
    ''' uncomment the following 2 lines to display the time required for partitioning
    'passedTime = (Second(Time) - Second(startTime)) + (Minute(Time) - Minute(startTime)) * 60
    'MsgBox "Partitioning done in " & passedTime & " seconds"
    
    ''' display the results on the appropriate sheets
    index = 1
    For i = 1 To elementNum
        For j = 1 To elementNum
            If IsEmpty(Worksheets("New Sequence").Cells(i, j + 1)) = False Then
                New_Seq(index) = Worksheets("New Sequence").Cells(i, j + 1)
                index = index + 1
            End If
        Next j
    Next i
    
    For i = 1 To elementNum
        Cells(2, i + 2) = New_Seq(i)
        Cells(i + 2, 2) = New_Seq(i)
        Cells(i + 2, 2).Interior.Color = Worksheets("DSM").Cells(New_Seq(i) + 1, 2).Interior.Color
        Cells(2, i + 2).Interior.Color = Worksheets("DSM").Cells(New_Seq(i) + 1, 2).Interior.Color
        
        tmpComment = Worksheets("DSM").Cells(New_Seq(i) + 1, 1).Comment.Text
        Cells(i + 2, 1) = Parameter(New_Seq(i))
        Cells(i + 2, 1).AddComment tmpComment
        Cells(i + 2, 1).Comment.Visible = 0
        
        Cells(1, i + 2) = Parameter(New_Seq(i))
        Cells(1, i + 2).AddComment tmpComment
        Cells(1, i + 2).Comment.Visible = 0
        
        Cells(i + 2, i + 2).AddComment tmpComment
        Cells(i + 2, i + 2).Comment.Visible = 0
        
        For j = 1 To elementNum
            Partitioned_DSM(i, j, 1) = DSM(New_Seq(i), New_Seq(j), 1)
            If (IsEmpty(Partitioned_DSM(i, j, 1)) = False) And (i <> j) Then
                Cells(i + 2, j + 2) = Partitioned_DSM(i, j, 1)
            End If
        Next j
    Next i
    
    For i = 1 To elementNum
        For j = i + 1 To elementNum
            If Cells(i + 2, j + 2).Value = 1 Then
                Range(Cells(i + 2, i + 2), Cells(j + 2, j + 2)).Select
                Selection.Interior.ColorIndex = 8
            End If
        Next j
    Next i
    
    For i = 1 To elementNum
        Cells(i + 2, i + 2).Select
        With Selection.Interior
            .ColorIndex = 1
            .Pattern = xlSolid
        End With
        Cells(i + 2, i + 2).Value = New_Seq(i)
        Selection.Font.ColorIndex = 2
    Next i

    Partitioned = 1 ' flag to indicate that the problem is partitioned now

End Sub


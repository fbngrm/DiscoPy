# DiscoPy

<img src="/icons/discopy.png" alt="DiscoPy" width="250px">

# Overview
  
[What is DiscoPy](#what-is-discoPy)
[How To](#how-to)
[Syntax Options](#syntax-options)
[Example](#example)
[User Interface](#user-interface)
[Installation](#installation)
[License](#license)
    
#What is DiscoPy
  
DiscoPy is a music file renamer and tagger that names files according to your preferred syntax. The meta data of your music files - like artist, labels, release date etc. - can be easily included in your naming scheme. If you like you can also download all corresponding artwork of a release with one click. 

DiscoPy uses the <a href="http://www.discogs.com">Discogs</a> database as source for the metadata and provides an (hopefully) easy to use graphical interface.
    
It is written in <a href="http://www.python.org">Python (2.7)</a> and uses <a href="https://riverbankcomputing.com/software/pyqt/intro">PyQt</a> for the UI.
Builds are available for Linux, Windows and Mac OS. See <a href="/discopy#installation">How to install DiscoPy</a> for more information.
    
#How To
  
**1. Drop your files**
  + Drop your files into the left table.
  + DiscoPy will guess the search query. It will appear in the *Release Name* text field.
  + DiscoPy will automatically search for the release if there is meta information available in your files.
 
**2. Search**
  + If the automatic search is not triggered, you can search manually.
  + Enter the release name, the Dicogs URL or the Barcode ID and hit the *Search* button.
  
**3. Enter the syntax**
  + Enter your preferred *Release Syntax* to compile the directory name.
  + Enter the *Track Syntax* to compile the names for the music files.
  + Hit enter to show the compiled names in the search result table (right table).
  + See <a href="#syntax-options">Syntax Options</a> for available syntax elements.
    
**4. Order your files**
  + All files in the left table will be renamed with the string of the corresponding row in the right table. **Make sure the order of your files (left table) correlates the order of the search results (right table)!**
  + Items can be sorted by drag and drop.
  + Items can be deleted by pressing return or delete.
  + Search result items can be edited by double clicking the text.
         
**5. Rename your files**
  + Rename your files by hitting the *Rename* button.
  + If something went wrong the renaming can be reverted by using the *Undo* button.
  + Tag your files by pressing the *Tag* button.
  + Download the artwork by pressing the *Artwork* button.


> Again: Make sure the order of your files in the left table correlates the order of the search results in the right table before renaming!


#Syntax Options
  
**Release Syntax**
+ The Release Syntax text field is used to compile the name for the directory that contains the music files.
    
**Release Syntax Keywords**

| Keyword | Rendered String             |
| --------|-----------------------------|      
| artist  | the lowercase artist name   |
| Artist  | the capitalized artist name |
| ARTIST  | the uppercase artist name   |
| release | the lowercase release name  |
| Release | the capitalized release name|
| RELEASE | the uppercase release name  |
| label   | the lowercase label names   |
| Label   | the capitalized label names |
| LABEL   | the uppercase label names   |
| country | the lowercase country name  |
| Country | the capitalized country name|
| COUNTRY | the uppercase country name  |
| genre   | the lowercase genre names   |
| Genre   | the capitalized genre names |
| GENRE   | the uppercase genre names   |
| year    | the release year            |
| Year    | the release year            |
| YEAR    | the release year            |

===

**Track Syntax**
+ The Track Syntax text field is used to compile the names for the music files.    
+ The syntax can be an abritrary alpha-numeric string and can contain special characters except for Discogs meta data, specific syntax keywords can be used that will be substituted by their corresponding value from the search results.
+ Press enter to update the search result table with the new syntax after modifying the syntax fileds.
    
**Track Syntx Keywords**

| Keyword | Rendered String             |
| --------|-----------------------------|     
| index   | the lowercase track index   |
| Index   | the capitalized track index |
| INDEX   | the uppercase track index   |
| track   | the lowercase track name    |
| Track   | the capitalized track name  |
| TRACK   | the uppercase track name    |
     
===
## Example
  
**Release Syntax**
    
| Existing Release/Folder Name | Release Syntax                 | New Release/Folder Name               |
| -----------------------------|--------------------------------|---------------------------------------| 
| kraftwerk_-_computer-world   | Artist - Release [year Lables] | Kraftwerk - Computer World [1981 Emi] |

**Track Syntax**

| Existing Track/File Name                              | Track Syntax         | New Track/File Name                         |
| ------------------------------------------------------|----------------------|---------------------------------------------| 
| Kraftwerk_-_Kraftwerk_07_it's_more_fun_to_compute.MP3 | index artist - track | 07 kraftwerk - it's more fun to compute.mp3 |
      
    
#User Interface
  <img src="/icons/start.png" alt="DiscoPy" >
  <img src="/icons/mainwindow.png" alt="DiscoPy" >
    
#Installation
You may want to install DiscoPy in a `virtualenv` containing PyQt4. After installing the dependencies with `pip install -e requirements.txt` you can run DiscoPy with `python discopy.py`.

#License
GNU - General Public License 3.0

    
    
    
  

  


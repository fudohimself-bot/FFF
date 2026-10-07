@echo off
rem Pull every file for FF16 character c1002 (candidate for Joshua) out of 0001.pac, then convert the textures to .dds.
rem Run this from the folder that contains FF16Tools.CLI.exe (the win-x64 folder). It only reads the game and writes to the OUT folder below.
rem Not yet run by the author: if a line fails, screenshot the black window and send it.

set "GAME=D:\steam\steamapps\common\FINAL FANTASY XVI\data"
set "OUT=joshua_extract"

if not exist "%GAME%\0001.pac" (
  echo Cannot find %GAME%\0001.pac - edit the GAME line at the top of this file.
  pause
  exit /b 1
)

FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/body.mdl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/material/m_c1002b0001_body_a.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/material/m_c1002b0001_body_b.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/material/m_c1002b0001_body_b_c01s.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/material/m_c1002b0001_body_c.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/material/m_c1002b0001_body_c_c01s.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/material/m_c1002b0001_body_torso.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_a_base.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_a_meta.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_a_norm.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_a_occl.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_a_roug.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_a_tile0_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_a_tile1_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_a_tile2_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_a_tile3_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_b_base.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_b_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_b_meta.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_b_norm.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_b_occl.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_b_roug.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_b_tile0_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_b_tile1_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_b_tile2_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_b_tile3_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_c_base.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_c_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_c_meta.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_c_norm.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_c_occl.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_c_roug.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_c_tile0_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_c_tile1_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_c_tile2_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_body_c_tile3_mask.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/body/b0001/texture/t_c1002b0001_torso_occl.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/face.mdl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/material/m_c1002f0101_buzz.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/material/m_c1002f0101_cuff.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/material/m_c1002f0101_eye.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/material/m_c1002f0101_face.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/material/m_c1002f0101_face_tears.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/material/m_c1002f0101_facehair.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/material/m_c1002f0101_innermouth.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/texture/t_c1002f0101_base.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/texture/t_c1002f0101_dirty_base.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/texture/t_c1002f0101_dirty_tear.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/texture/t_c1002f0101_frown_norm.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/texture/t_c1002f0101_frown_occl.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/texture/t_c1002f0101_norm.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/texture/t_c1002f0101_occl.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/texture/t_c1002f0101_scream_norm.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/face/f0101/texture/t_c1002f0101_scream_occl.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/head/h0101/head.mdl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/head/h0101/material/m_c1002h0101_hair_a.mtl -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/model/head/h0101/texture/t_c1002h0101_occl.tex -o "%OUT%"
FF16Tools.CLI.exe unpack -i "%GAME%\0001.pac" -f chara/c1002/pack/c1002.pac -o "%OUT%"

echo Converting textures to .dds ...
FF16Tools.CLI.exe tex-conv -i "%OUT%"

echo Done. Asked for 58 files. Look inside the %OUT% folder.
pause

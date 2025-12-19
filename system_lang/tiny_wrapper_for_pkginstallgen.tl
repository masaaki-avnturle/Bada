# tiny_wrapper_for_pkginstallgen.tl
cmd_file <- "/tmp/tiny_commands.txt"
out_file <- "/tmp/pkginstall_out.txt"

safe_read := func(p) { try { return file_read(p) } catch { return null } }
safe_write := func(p,t) { try { file_write(p,t) } catch { } }
exists := func(p) { try { return file_exists(p) } catch { return false } }

trim_newlines := func(s) { if s==null { return "" } ; r := s ; while len(r)>0 and (r[-1]=='\n' or r[-1]=='\r') { r := r[0:len(r)-1] } ; return r }

dispatch := func(line) {
		      if line == null { return false }
		          s := trim_newlines(line)
				         if s == "" { return false }
			         # expected: compute <module> <path>
			         parts := split(s, " ")
						    if len(parts) >= 3 and parts[0]=="compute" {
							            mod := parts[1]
										         path := parts[2]
											         # call external binary; if system() not available, user should run:
											         # ./pkginstallgen --module=<mod> --file=<path> > /tmp/pkginstall_out.txt
											         # Here we attempt to use run(...) if available; otherwise instruct user.
											         try {
													             run("./pkginstallgen --module=" + mod + " --file=" + path + " > " + out_file)
															                 res := safe_read(out_file)
																	             print("[RESULT] " + (if res==null then "no output" else res))
																		             } catch {
																				                 print("Cannot invoke binary from tiny_lang in this environment. Run manually:")
																							             print("./pkginstallgen --module=" + mod + " --file=" + path + " > " + out_file)
																								                 print("Then read " + out_file)
																										         }
									         return false
											     }
					    if s == "help" { print("Commands: compute <module> <file>, help, quit") ; return false }
					        if s == "quit" { print("Quit requested.") ; return true }
						    print("Unknown command: " + s)
							        return false
	  }

main := func() {
	          if not exists(cmd_file) { safe_write(cmd_file, "") }
		      print("tiny wrapper started. Append commands to " + cmd_file)
			          processed := 0
				      while true {
					              content := safe_read(cmd_file)
								               if content == null { content := "" }
							               lines := split(content, "\n")
										              i := processed
											              quit_flag := false
												              while i < len(lines) {
														                  l := trim_newlines(lines[i])
																	                 if l != "" {
																				                 print("[EXEC] " + l)
																							                 ok := false
																									                 try { ok := dispatch(l) } catch { ok := false ; print("[ERR] dispatch error for: " + l) }
																						                 if ok { quit_flag := true ; break }
																								             }
																                 i := i + 1
																			            }
									              processed := len(lines)
													         if quit_flag { break }
												         try { sleep(1) } catch { try { _ := safe_read(out_file) } catch { } }
													     }
		          print("Daemon exiting.")
      }

main()

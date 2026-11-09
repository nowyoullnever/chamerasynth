// Phase 5, offline-only. Export WAV-resource handle references and reachable
// functions. Logical VA/file mapping remains an analysis hypothesis.
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;

public class ExportPhase5Audio extends GhidraScript {
    private static final long BIAS = 0x200;
    private static final long RESOURCE_INIT = 0x1e234;
    private static final long HANDLE_TABLE_LITERAL = 0x1e290;
    private static final long[] BASE_TARGETS = {
        0x1e234, 0x1310, 0x1298, 0x1e844, 0x1f560, 0x130c0, 0x1e18c, 0x173c,
        0x25984, 0x12f0c, 0x129a4, 0x12e48, 0x1372c, 0x135bc, 0x13638,
        0x33d74, 0x33f58, 0x33f70, 0x33970
    };
    private static final long[] AUDIO_LITERALS = {0x1e280, 0x1e284, 0x1e288, 0x1e28c, 0x1e290, 0x1ec98};
    private static String q(String s) { return s == null ? "null" : "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\""; }
    private static String va(Address a) { return a == null ? null : String.format("0x%08x", a.getOffset()); }
    private static String file(long v) { return String.format("0x%06x", v + BIAS); }
    private Address at(long v) { return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v); }
    private String raw(Address a, int n) throws Exception { byte[] b = new byte[n]; currentProgram.getMemory().getBytes(a,b); StringBuilder s=new StringBuilder(); for(byte x:b)s.append(String.format("%02x",x&255)); return s.toString(); }
    private List<String> refs(Address a) { List<String> out=new ArrayList<>(); for(Reference r:currentProgram.getReferenceManager().getReferencesTo(a))out.add(va(r.getFromAddress())+"->"+va(r.getToAddress())+":"+r.getReferenceType()); return out; }
    private List<String> calls(Function f) { List<String> out=new ArrayList<>(); InstructionIterator it=currentProgram.getListing().getInstructions(f.getBody(),true); while(it.hasNext()){Instruction i=it.next();if(i.getFlowType().isCall())for(Address to:i.getFlows())out.add(va(i.getAddress())+"->"+va(to));}return out; }
    private void arr(PrintWriter p,List<String> items){p.print("[");for(int i=0;i<items.size();i++){if(i>0)p.print(",");p.print(q(items.get(i)));}p.print("]");}
    @Override public void run() throws Exception {
        if(getScriptArgs().length!=1)throw new IllegalArgumentException("expected export dir");
        File root=new File(getScriptArgs()[0]);root.mkdirs(); File pseudo=new File(root,"pseudocode");pseudo.mkdirs();
        long table=currentProgram.getMemory().getInt(at(HANDLE_TABLE_LITERAL)) & 0xffffffffL;
        long[] fields={table+4,table+6,table+8,table+12,table+14};
        Set<Long> targets=new LinkedHashSet<>();for(long x:BASE_TARGETS)targets.add(x);
        List<String> handleRows=new ArrayList<>();
        for(long field:fields){Address a=at(field); List<String> r=refs(a); for(Reference ref:currentProgram.getReferenceManager().getReferencesTo(a)){Function f=currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());if(f!=null)targets.add(f.getEntryPoint().getOffset());} StringBuilder row=new StringBuilder("{\"field_va\":").append(q(va(a))).append(",\"field_width\":\"uint16 candidate\",\"references\":[");for(int i=0;i<r.size();i++){if(i>0)row.append(',');row.append(q(r.get(i)));}row.append("]}");handleRows.add(row.toString());}
        List<String> literalRows=new ArrayList<>();
        for(long literal:AUDIO_LITERALS){long value=currentProgram.getMemory().getInt(at(literal))&0xffffffffL;List<String> r=refs(at(value));for(Reference ref:currentProgram.getReferenceManager().getReferencesTo(at(value))){Function f=currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());if(f!=null)targets.add(f.getEntryPoint().getOffset());}StringBuilder row=new StringBuilder("{\"literal_va\":").append(q(va(at(literal)))).append(",\"value\":").append(q(String.format("0x%08x",value))).append(",\"value_references\":[");for(int i=0;i<r.size();i++){if(i>0)row.append(',');row.append(q(r.get(i)));}row.append("]}");literalRows.add(row.toString());}
        DecompInterface d=new DecompInterface();d.setSimplificationStyle("decompile");d.openProgram(currentProgram);
        try(PrintWriter out=new PrintWriter(new FileWriter(new File(root,"audio_handle_graph.json")))){
            out.print("{\"mapping\":\"file offset = logical VA + 0x200; hypothesis only\",\"handle_table_literal_va\":");out.print(q(va(at(HANDLE_TABLE_LITERAL))));out.print(",\"handle_table_value\":");out.print(q(String.format("0x%08x",table)));out.print(",\"handle_fields\":[");for(int i=0;i<handleRows.size();i++){if(i>0)out.print(',');out.print(handleRows.get(i));}out.print("],\"audio_literals\":[");for(int i=0;i<literalRows.size();i++){if(i>0)out.print(',');out.print(literalRows.get(i));}out.println("],\"functions\":[");
            boolean first=true;for(long target:targets){Address a=at(target);Function f=currentProgram.getFunctionManager().getFunctionContaining(a);if(!first)out.println(',');first=false;out.print("{\"requested_va\":"+q(va(a))+",\"requested_file_offset\":"+q(file(target)));if(f==null){out.print(",\"status\":\"no_function\"}");continue;}DecompileResults dr=d.decompileFunction(f,90,monitor);String stem=String.format("%06x",f.getEntryPoint().getOffset()+BIAS);try(PrintWriter c=new PrintWriter(new FileWriter(new File(pseudo,stem+".c")))){c.println("/* Phase 5 focused audio export; inferred decompiler output. */");c.println(dr.getDecompiledFunction()==null?"/* no pseudocode */":dr.getDecompiledFunction().getC());}out.print(",\"entry_va\":"+q(va(f.getEntryPoint()))+",\"entry_file_offset\":"+q(file(f.getEntryPoint().getOffset()))+",\"head_hex\":"+q(raw(f.getEntryPoint(),32))+",\"incoming_references\":");arr(out,refs(f.getEntryPoint()));out.print(",\"direct_call_edges\":");arr(out,calls(f));out.print(",\"pseudocode_file\":"+q("pseudocode/"+stem+".c")+",\"decompile_status\":"+q(dr.decompileCompleted()?"complete":"incomplete")+"}");}
            out.println("],\"limitations\":[\"Direct references only; computed dataflow and runtime audio state can be absent.\",\"No audio hardware or firmware execution was performed.\"]}");
        } finally {d.dispose();}
    }
}

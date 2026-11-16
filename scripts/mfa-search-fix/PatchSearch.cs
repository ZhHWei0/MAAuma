// Local compatibility fix for MFAAvalonia 2.15.2 / SukiUI 2.0.0.
// Equivalent source change in ComboBoxExtensions.OnCanSearchChanged:
// if (args.NewValue.Value)
//     comboBox.ItemsPanel = new FuncTemplate<Panel>(() => new StackPanel());
// Keep ItemsSource and original indices intact: MFA saves the original case index.
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using Mono.Cecil;
using Mono.Cecil.Cil;

internal static class PatchSearch
{
    private const string OriginalHash = "E025C9F5138F1751039F56FBDAB0F2746A99A131C7846A21B12E321B647BFD2D";
    private const string Marker = "MaaUma_CreateSearchPanel";

    public static int Main(string[] args)
    {
        try
        {
            if (args.Length != 3) throw new ArgumentException("Usage: PatchSearch <SukiUI.dll> <Avalonia.Controls.dll> <output.dll>");
            using var assembly = AssemblyDefinition.ReadAssembly(args[0]);
            var module = assembly.MainModule;
            var extension = module.Types.Single(t => t.FullName == "SukiUI.Extensions.ComboBoxExtensions");
            if (extension.Methods.Any(m => m.Name == Marker))
                throw new InvalidOperationException("Search patch already installed.");
            if (Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(args[0]))) != OriginalHash)
                throw new InvalidOperationException("Unsupported SukiUI build. This patch only supports the verified MFA 2.15.2 DLL.");
            if (assembly.Name.HasPublicKey) throw new InvalidOperationException("Cannot patch a signed DLL.");

            using var controls = AssemblyDefinition.ReadAssembly(args[1]);
            var types = controls.MainModule.Types;
            var panel = types.Single(t => t.FullName == "Avalonia.Controls.Panel");
            var stack = types.Single(t => t.FullName == "Avalonia.Controls.StackPanel");
            var combo = types.Single(t => t.FullName == "Avalonia.Controls.ComboBox");
            var itemsControl = types.Single(t => t.FullName == "Avalonia.Controls.ItemsControl");
            var constructors = combo.Methods.Single(m => m.Name == ".cctor").Body.Instructions
                .Where(i => i.OpCode == OpCodes.Newobj).Select(i => (MethodReference)i.Operand).ToArray();
            var funcCtor = constructors.Single(m => m.DeclaringType.FullName == "System.Func`1<Avalonia.Controls.Panel>");
            var templateCtor = constructors.Single(m => m.DeclaringType.FullName == "Avalonia.Controls.Templates.FuncTemplate`1<Avalonia.Controls.Panel>");

            var factory = new MethodDefinition(Marker, MethodAttributes.Private | MethodAttributes.Static,
                module.ImportReference(panel));
            factory.Body.Instructions.Add(Instruction.Create(OpCodes.Newobj,
                module.ImportReference(stack.Methods.Single(m => m.Name == ".ctor" && m.Parameters.Count == 0))));
            factory.Body.Instructions.Add(Instruction.Create(OpCodes.Ret));
            extension.Methods.Add(factory);

            var changed = extension.Methods.Single(m => m.Name == "OnCanSearchChanged");
            // This verified build branches to the disabled case immediately after reading NewValue.Value.
            var enabledBranch = changed.Body.Instructions.First(i => i.OpCode == OpCodes.Brfalse_S);
            var insertionPoint = enabledBranch.Next;
            if (insertionPoint.OpCode != OpCodes.Ldloc_0)
                throw new InvalidOperationException("Unexpected handler layout; patch aborted.");
            var il = changed.Body.GetILProcessor();
            foreach (var instruction in new[] {
                Instruction.Create(OpCodes.Ldloc_0),
                Instruction.Create(OpCodes.Ldnull),
                Instruction.Create(OpCodes.Ldftn, factory),
                Instruction.Create(OpCodes.Newobj, module.ImportReference(funcCtor)),
                Instruction.Create(OpCodes.Newobj, module.ImportReference(templateCtor)),
                Instruction.Create(OpCodes.Callvirt, module.ImportReference(itemsControl.Methods.Single(m => m.Name == "set_ItemsPanel")))
            }) il.InsertBefore(insertionPoint, instruction);

            module.Mvid = Guid.NewGuid();
            assembly.Write(args[2]);
            Console.WriteLine("Patched searchable ComboBoxes to realize all items; item identities and indices are unchanged.");
            return 0;
        }
        catch (Exception error) { Console.Error.WriteLine(error.Message); return 1; }
    }
}
